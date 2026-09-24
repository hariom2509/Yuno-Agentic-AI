import json
import logging
from datetime import datetime
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.message import Message
from app.runtime.checkpointer import checkpointer as _checkpointer
from app.runtime.idempotency import IdempotencyGuard
from app.runtime.tool_executor import ToolExecutor
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# MCP tool names that ALWAYS require human approval (regardless of node config).
# These are high-risk destructive operations that should never run unattended.
ALWAYS_REQUIRE_APPROVAL = {
    "mcp::github-mcp::delete_repository",
    "mcp::postgres-mcp::drop_table",
    "mcp::postgres-mcp::truncate_table",
}


class AgentState(TypedDict):
    task: str
    history: list[dict]
    current_output: str
    tokens_used: int
    cost_usd: float


class RuntimeEngine:

    @staticmethod
    def execute_workflow(db: Session, workflow, input_task: str = None) -> Execution:
        """
        Parses the workflow graph JSON, builds a LangGraph StateGraph with
        production checkpointing, executes it, and persists results.

        New in this version:
          - builder.compile(checkpointer=_checkpointer) for durable execution
          - thread_id = str(execution.id) for checkpoint isolation
          - HITL interrupt detection: status → "waiting_for_approval"
          - Idempotency keys protect side-effecting MCP tools from replay
        """
        task = input_task or "Analyze OpenAI vs Anthropic enterprise positioning"

        execution = Execution(
            workflow_id=workflow.id,
            status="running",
            current_node="Starting",
            input_task=task,
            started_at=datetime.utcnow(),
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        RuntimeEngine._dispatch(db, execution.id, "Human", "Coordinator", task, "human")

        try:
            graph_def = workflow.graph or {}
            nodes = graph_def.get("nodes", [])
            edges = graph_def.get("edges", [])

            if not nodes:
                result = RuntimeEngine._run_default_workflow(db, execution, task)
            else:
                result = RuntimeEngine._run_graph_workflow(db, execution, task, nodes, edges)

            # --- Handle HITL interrupt (execution paused, not failed) ---
            if result.get("hitl_interrupt"):
                interrupt_data = result["hitl_interrupt"]
                execution.status = "waiting_for_approval"
                execution.current_node = interrupt_data.get("node", "Paused")
                execution.approval_data = json.dumps(interrupt_data)
                execution.tokens_used = result.get("tokens", 0)
                execution.cost_usd = result.get("cost", 0.0)
                # Do NOT set final_output or completed_at — execution continues on resume
            else:
                execution.status = "completed"
                execution.current_node = "Completed"
                execution.final_output = result["output"]
                execution.tokens_used = result.get("tokens", 0)
                execution.cost_usd = result.get("cost", 0.0)
                execution.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {e}")
            execution.status = "failed"
            execution.current_node = "Failed"
            execution.final_output = f"Execution failed: {str(e)}"
            execution.completed_at = datetime.utcnow()

            try:
                from app.services.failure_policy_service import FailurePolicyService
                logger.info(f"Invoking failure policy handler for failed execution #{execution.id}")
                FailurePolicyService.handle_workflow_failure(db, execution)
            except Exception as auto_err:
                logger.error(f"Failure policy execution error: {auto_err}")

        db.commit()

        try:
            from app.websocket.manager import broadcast_sync
            broadcast_sync({
                "type": "execution_update",
                "execution_id": execution.id,
                "status": execution.status,
                "output": execution.final_output,
                "tokens": execution.tokens_used,
                "cost": execution.cost_usd,
            })
        except Exception:
            pass

        return execution

    # -------------------------------------------------------------------------
    # Graph Building — extracted so resume_workflow can reuse the same structure
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_graph(
        db: Session,
        execution: Execution,
        task: str,
        nodes: list,
        edges: list,
        token_counter: dict,
    ):
        """
        Compiles a LangGraph StateGraph from ReactFlow node/edge definitions.

        Key production features wired here:
          1. Checkpointing  — builder.compile(checkpointer=_checkpointer)
                              Every node completion saves a checkpoint keyed by thread_id.
          2. HITL interrupt — interrupt() called for nodes with require_approval=True
                              or for tools in ALWAYS_REQUIRE_APPROVAL set.
          3. Idempotency    — SHA-256 key checked/registered before each MCP tool call.
          4. Memory         — Redis-backed conversation history recalled/stored per agent.
          5. Guardrails     — Input and output content filtering per node config.

        Args:
            token_counter: Mutable dict {"tokens": int, "cost": float} for
                           cross-node accumulation. Use {"tokens":0,"cost":0.0} for new runs,
                           or carry existing totals for resume.

        Returns:
            Tuple of (compiled_graph, initial_state, config)
        """
        from app.runtime.guardrails import Guardrails
        from app.runtime.memory_manager import memory

        # Build adjacency map: source → [(target, condition), ...]
        adjacency: dict = {}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            cond = (edge.get("data", {}) or {}).get("condition", "").lower()
            if src and tgt:
                adjacency.setdefault(src, []).append((tgt, cond))

        # Find start node (no incoming edges)
        all_targets = {e.get("target") for e in edges}
        start_nodes = [n for n in nodes if n.get("id") not in all_targets]
        if not start_nodes:
            start_nodes = nodes[:1]

        node_map = {n["id"]: n for n in nodes}
        builder = StateGraph(AgentState)

        for node in nodes:
            node_id = node["id"]
            node_data = node.get("data", {})
            node_type = node_data.get("type", "agent")
            label = node_data.get("label", node_id)

            def make_node_fn(nid, ndata, nlabel, ntype):
                def node_fn(state: AgentState) -> AgentState:
                    # --- State & DB update ---
                    execution.current_node = nlabel
                    db.commit()

                    current_input = state.get("current_output") or state.get("task", "")
                    guardrails_config = ndata.get("guardrails", {})

                    # --- Guardrails: Input ---
                    input_check = Guardrails.check_input(current_input, guardrails_config)
                    if not input_check.passed:
                        current_input = f"System Error: {input_check.reason}"
                        RuntimeEngine._dispatch(db, execution.id, "System", nlabel, current_input, "system")

                    RuntimeEngine._dispatch(
                        db, execution.id, "System", nlabel,
                        f"Executing node: {nlabel}", "system"
                    )

                    if ntype == "tool":
                        tool_name = ndata.get("tool", "web_search")
                        require_approval = ndata.get("require_approval", False)

                        # Query CapabilityRegistry for DB-level risk & approval policy
                        try:
                            from app.services.capability_registry import CapabilityRegistry
                            policy = CapabilityRegistry.get_execution_policy(db, tool_name)
                            db_requires_approval = policy.get("requires_approval", False)
                        except Exception:
                            db_requires_approval = False

                        needs_approval = require_approval or db_requires_approval or (tool_name in ALWAYS_REQUIRE_APPROVAL)
                        if needs_approval:
                            human_decision = interrupt({
                                "status": "WAITING_FOR_APPROVAL",
                                "node": nlabel,
                                "tool": tool_name,
                                "message": (
                                    f"Node '{nlabel}' requests execution of tool '{tool_name}'. "
                                    f"Review and approve or reject."
                                ),
                                "execution_id": execution.id,
                            })
                            # human_decision receives the Command(resume=...) value on graph resume
                            if human_decision != "APPROVED":
                                output = f"[HITL Rejected] Human denied execution of '{tool_name}'."
                                RuntimeEngine._dispatch(db, execution.id, nlabel, "Human", output, "system")
                                new_history = state.get("history", []) + [{"node": nlabel, "output": output}]
                                return {
                                    **state,
                                    "current_output": output,
                                    "history": new_history,
                                    "tokens_used": token_counter["tokens"],
                                    "cost_usd": token_counter["cost"],
                                }

                        # --- Idempotency: shield MCP side-effecting tools from duplicate calls ---
                        # Key = SHA-256("{execution_id}:{node_id}:{tool_name}")[:16]
                        # Prevents re-execution when graph replays from checkpoint on resume.
                        if tool_name.startswith("mcp::"):
                            idem_key = IdempotencyGuard.compute_key(execution.id, nid, tool_name)
                            if IdempotencyGuard.is_executed(idem_key):
                                output = (
                                    f"[Idempotency Shield] '{tool_name}' already executed "
                                    f"(key: {idem_key[:8]}…). Skipping duplicate."
                                )
                                RuntimeEngine._dispatch(db, execution.id, nlabel, "System", output, "system")
                                new_history = state.get("history", []) + [{"node": nlabel, "output": output}]
                                return {
                                    **state,
                                    "current_output": output,
                                    "history": new_history,
                                    "tokens_used": token_counter["tokens"],
                                    "cost_usd": token_counter["cost"],
                                }
                            # Mark BEFORE the call to prevent double-fire if process is killed mid-call
                            IdempotencyGuard.mark_executed(idem_key)

                        output = ToolExecutor.execute(tool_name, current_input, db)
                        msg_type = "tool"

                    else:
                        # --- Agent node: Redis memory + Groq-routed LLM ---
                        from app.models.agent import Agent
                        # Prefer agent_id stored directly in node data (set by Builder).
                        # Fall back to name-based lookup for backward compatibility.
                        agent_id = ndata.get("agent_id")
                        if agent_id is None:
                            agent_row = db.query(Agent).filter(Agent.name == nlabel).first()
                            agent_id = agent_row.id if agent_row else None

                        sys_prompt = ndata.get(
                            "system_prompt",
                            f"You are {nlabel}. Complete the given task thoughtfully."
                        )
                        model = ndata.get("model", "llama-3.1-8b-instant")
                        temperature = ndata.get("temperature", 0.7)
                        memory_enabled = ndata.get("memory_enabled", True)

                        context_key = str(execution.id)
                        history = memory.recall(nlabel, context_key) if memory_enabled else []

                        # Dynamic Category Router & Server Tool Scoping
                        from app.services.capability_registry import CapabilityRegistry
                        scoped_info = CapabilityRegistry.classify_and_scope_tools(db, current_input)
                        scoped_tools = scoped_info.get("tools", [])

                        result = OpenAIService.chat(
                            system_prompt=sys_prompt,
                            user_prompt=current_input,
                            model=model,
                            temperature=temperature,
                            messages_history=history,
                            tools=scoped_tools if scoped_tools else None,
                        )
                        output = result["content"]

                        # Handle LLM Tool Call if generated
                        tool_calls = result.get("tool_calls")
                        if tool_calls and len(tool_calls) > 0:
                            first_call = tool_calls[0]
                            tc_func = getattr(first_call, "function", None)
                            if tc_func:
                                tool_name = tc_func.name
                                raw_args = tc_func.arguments
                                try:
                                    args_dict = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                                except Exception:
                                    args_dict = {"query": current_input}

                                canonical_tool = CapabilityRegistry.resolve_canonical_name(tool_name)
                                policy = CapabilityRegistry.get_execution_policy(db, canonical_tool) or {}
                                db_requires_approval = policy.get("requires_approval", False) or (policy.get("risk_level") in ["HIGH", "CRITICAL"])
                                needs_approval = db_requires_approval or (canonical_tool in ALWAYS_REQUIRE_APPROVAL) or ("truncate" in tool_name.lower()) or ("drop" in tool_name.lower())

                                if needs_approval:
                                    human_decision = interrupt({
                                        "status": "WAITING_FOR_APPROVAL",
                                        "node": nlabel,
                                        "tool": canonical_tool,
                                        "message": (
                                            f"Agent '{nlabel}' dynamically selected high-risk tool '{canonical_tool}'. "
                                            f"Review and approve or reject database mutation."
                                        ),
                                        "execution_id": execution.id,
                                    })
                                    if human_decision != "APPROVED":
                                        output = f"[HITL Rejected] Human denied execution of '{canonical_tool}'."
                                    else:
                                        tool_res = ToolExecutor.execute(canonical_tool, args_dict, db=db, agent_id=agent_id)
                                        output = f"Executed '{canonical_tool}' ({scoped_info['category']} mode after approval):\n{tool_res}"
                                else:
                                    tool_res = ToolExecutor.execute(canonical_tool, args_dict, db=db, agent_id=agent_id)
                                    output = f"Executed '{canonical_tool}' ({scoped_info['category']} mode):\n{tool_res}"

                        token_counter["tokens"] += result["total_tokens"]
                        token_counter["cost"] += result["cost_usd"]
                        msg_type = "agent"

                        if memory_enabled:
                            memory.store(nlabel, "user", current_input, context_key)
                            memory.store(nlabel, "assistant", output, context_key)

                    # --- Guardrails: Output ---
                    output_check = Guardrails.check_output(output, guardrails_config)
                    output = output_check.filtered_content if output_check.passed else f"Output blocked: {output_check.reason}"

                    next_nodes = adjacency.get(nid, [])
                    receiver = (
                        node_map.get(next_nodes[0][0], {}).get("data", {}).get("label", "Human")
                        if next_nodes else "Human"
                    )
                    RuntimeEngine._dispatch(db, execution.id, nlabel, receiver, output, msg_type)

                    return {
                        **state,
                        "current_output": output,
                        "history": state.get("history", []) + [{"node": nlabel, "output": output}],
                        "tokens_used": token_counter["tokens"],
                        "cost_usd": token_counter["cost"],
                    }
                return node_fn

            builder.add_node(node_id, make_node_fn(node_id, node_data, label, node_type))

        # --- Wire edges ---
        start_id = start_nodes[0]["id"]
        builder.set_entry_point(start_id)

        for node in nodes:
            nid = node["id"]
            targets = adjacency.get(nid, [])
            if not targets:
                builder.add_edge(nid, END)
            elif len(targets) == 1 and not targets[0][1]:
                builder.add_edge(nid, targets[0][0])
            else:
                # Conditional routing: substring-match on current_output
                def make_routing_fn(t_list):
                    def route(state: AgentState):
                        output_lower = state.get("current_output", "").lower()
                        for target_id, condition in t_list:
                            if condition and condition in output_lower:
                                return target_id
                        return t_list[0][0]  # fallback: first target
                    return route
                route_map = {tgt: tgt for tgt, _ in targets}
                builder.add_conditional_edges(nid, make_routing_fn(targets), route_map)

        # --- Compile WITH checkpointer ---
        # This single change enables: durable execution, HITL pause/resume,
        # state history queries, and crash recovery from last checkpoint.
        compiled = builder.compile(checkpointer=_checkpointer)

        # thread_id scopes checkpoints to this execution.
        # Each execution_id is unique (PK), so threads never collide.
        thread_id = str(execution.id)
        execution.thread_id = thread_id

        # recursion_limit: max(node.max_iterations across all nodes) + 5 buffer
        max_iter = 10
        for n in nodes:
            nm = (n.get("data") or {}).get("max_iterations")
            if nm:
                try:
                    max_iter = max(max_iter, int(nm))
                except (ValueError, TypeError):
                    pass

        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": max_iter + 5,
        }

        initial_state: AgentState = {
            "task": task,
            "history": [],
            "current_output": task,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }

        return compiled, initial_state, config

    # -------------------------------------------------------------------------
    # Graph Execution
    # -------------------------------------------------------------------------

    @staticmethod
    def _run_graph_workflow(
        db: Session, execution: Execution, task: str, nodes: list, edges: list
    ) -> dict:
        """
        Executes a user-defined ReactFlow graph with full LangGraph integration.
        Returns a result dict with "output", "tokens", "cost", and optionally "hitl_interrupt".
        """
        token_counter = {"tokens": 0, "cost": 0.0}
        compiled, initial_state, config = RuntimeEngine._build_graph(
            db, execution, task, nodes, edges, token_counter
        )

        # Persist thread_id BEFORE execution so resume_workflow can find it
        # even if execution is killed mid-graph.
        db.commit()

        final_state = compiled.invoke(initial_state, config)

        # --- HITL Detection ---
        # After invoke() returns, check if execution is paused at an interrupt() call.
        # state_snap.next is non-empty when there are pending (unfinished) nodes.
        try:
            state_snap = compiled.get_state(config)
            if state_snap.next:
                # Extract the interrupt payload stored by interrupt({...})
                interrupt_data: dict = {}
                for task_obj in state_snap.tasks:
                    if hasattr(task_obj, "interrupts") and task_obj.interrupts:
                        interrupt_data = task_obj.interrupts[0].value
                        break

                return {
                    "output": None,
                    "tokens": token_counter["tokens"],
                    "cost": token_counter["cost"],
                    "hitl_interrupt": interrupt_data or {
                        "status": "WAITING_FOR_APPROVAL",
                        "node": str(state_snap.next),
                        "execution_id": execution.id,
                    },
                }
        except Exception as snap_err:
            logger.warning(f"State snapshot check failed (non-fatal): {snap_err}")

        # --- Normal completion ---
        from app.tools.report_generator_tool import generate_report
        raw_output = final_state.get("current_output", "No output")
        final_output = raw_output if str(raw_output).startswith("# AI Analysis Report") else generate_report(raw_output)

        return {
            "output": final_output,
            "tokens": final_state.get("tokens_used", token_counter["tokens"]),
            "cost": final_state.get("cost_usd", token_counter["cost"]),
        }

    # -------------------------------------------------------------------------
    # HITL Resume
    # -------------------------------------------------------------------------

    @staticmethod
    def resume_workflow(db: Session, execution: Execution, decision: str) -> Execution:
        """
        Resumes a HITL-paused execution after a human decision.

        How it works:
          1. Recompiles the same graph structure from the workflow JSON.
             (Graph structure is stateless — the checkpointer holds the state.)
          2. Calls graph.invoke(Command(resume=decision), config) with the same
             thread_id. LangGraph loads the checkpoint, delivers `decision` as
             the return value of the interrupt() call, and continues execution.
          3. Checks for another interrupt (chained HITL) or normal completion.

        Args:
            db:       Active SQLAlchemy session
            execution: Execution with status="waiting_for_approval"
            decision: "APPROVED" or "REJECTED"

        Returns:
            Updated Execution with new status.
        """
        from app.services.workflow_service import WorkflowService

        workflow = WorkflowService.get_workflow_by_id(db, execution.workflow_id)
        if not workflow:
            execution.status = "failed"
            execution.final_output = "Resume failed: workflow record not found."
            execution.completed_at = datetime.utcnow()
            db.commit()
            return execution

        graph_def = workflow.graph or {}
        nodes = graph_def.get("nodes", [])
        edges = graph_def.get("edges", [])

        if not nodes:
            execution.status = "failed"
            execution.final_output = "Resume failed: workflow has no graph nodes."
            execution.completed_at = datetime.utcnow()
            db.commit()
            return execution

        # Carry forward accumulated tokens/cost from the paused phase
        token_counter = {
            "tokens": execution.tokens_used or 0,
            "cost": execution.cost_usd or 0.0,
        }

        try:
            compiled, _, config = RuntimeEngine._build_graph(
                db, execution, execution.input_task or "", nodes, edges, token_counter
            )

            execution.status = "running"
            execution.approval_data = None
            db.commit()

            RuntimeEngine._dispatch(
                db, execution.id, "Human", "System",
                f"Execution resumed with decision: {decision}", "human"
            )

            # LangGraph loads checkpoint for thread_id and resumes from interrupt() call.
            # The `decision` string becomes the return value of interrupt() in the node.
            final_state = compiled.invoke(Command(resume=decision), config)

            # Check for another HITL interrupt in the resumed execution
            state_snap = compiled.get_state(config)
            logger.info(f"DEBUG RESUME execution #{execution.id}: next={state_snap.next}, tasks={state_snap.tasks}")
            if state_snap.next:
                interrupt_data: dict = {}
                for task_obj in state_snap.tasks:
                    if hasattr(task_obj, "interrupts") and task_obj.interrupts:
                        interrupt_data = task_obj.interrupts[0].value
                        break

                execution.status = "waiting_for_approval"
                execution.current_node = interrupt_data.get("node", "Paused")
                execution.approval_data = json.dumps(interrupt_data or {"status": "WAITING_FOR_APPROVAL"})
            else:
                from app.tools.report_generator_tool import generate_report
                raw = final_state.get("current_output", "Resumed execution completed.")
                final_output = raw if str(raw).startswith("# AI Analysis Report") else generate_report(raw)

                execution.status = "completed"
                execution.current_node = "Completed"
                execution.final_output = final_output
                execution.tokens_used = final_state.get("tokens_used", token_counter["tokens"])
                execution.cost_usd = final_state.get("cost_usd", token_counter["cost"])
                execution.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Resume of execution #{execution.id} failed: {e}")
            execution.status = "failed"
            execution.current_node = "Failed"
            execution.final_output = f"Resume failed: {str(e)}"
            execution.completed_at = datetime.utcnow()

        db.commit()

        try:
            from app.websocket.manager import broadcast_sync
            broadcast_sync({
                "type": "execution_update",
                "execution_id": execution.id,
                "status": execution.status,
                "output": execution.final_output,
                "tokens": execution.tokens_used,
                "cost": execution.cost_usd,
            })
        except Exception:
            pass

        return execution

    # -------------------------------------------------------------------------
    # Default 3-Agent Pipeline (no graph configured)
    # -------------------------------------------------------------------------

    @staticmethod
    def _run_default_workflow(db: Session, execution: Execution, task: str) -> dict:
        """
        Default research → analysis → report pipeline.
        Runs when workflow.graph has no nodes.
        """
        total_tokens = 0
        total_cost = 0.0

        execution.current_node = "Research Agent"
        db.commit()
        RuntimeEngine._dispatch(db, execution.id, "Coordinator", "Research Agent", task, "agent")

        research_data = ToolExecutor.execute("web_search", task, db)
        RuntimeEngine._dispatch(db, execution.id, "Research Agent", "Analysis Agent", research_data, "tool")

        execution.current_node = "Analysis Agent"
        db.commit()

        analysis_result = OpenAIService.chat(
            system_prompt=(
                "You are a senior AI business analyst. "
                "Analyze the research data provided and extract key insights, competitive positioning, "
                "market trends, and strategic implications. Be specific and data-driven."
            ),
            user_prompt=f"Task: {task}\n\nResearch Data:\n{research_data}",
            model="gpt-3.5-turbo",
        )
        total_tokens += analysis_result["total_tokens"]
        total_cost += analysis_result["cost_usd"]
        RuntimeEngine._dispatch(db, execution.id, "Analysis Agent", "Report Agent", analysis_result["content"], "agent")

        execution.current_node = "Report Agent"
        db.commit()

        from app.tools.report_generator_tool import generate_report
        final_report = generate_report(analysis_result["content"])
        RuntimeEngine._dispatch(db, execution.id, "Report Agent", "Human", final_report, "agent")

        return {"output": final_report, "tokens": total_tokens, "cost": total_cost}

    # -------------------------------------------------------------------------
    # Message Dispatch
    # -------------------------------------------------------------------------

    @staticmethod
    def _dispatch(
        db: Session,
        execution_id: int,
        sender: str,
        receiver: str,
        content: str,
        message_type: str = "agent",
    ) -> Message:
        msg = Message(
            execution_id=execution_id,
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        try:
            from app.websocket.manager import broadcast_sync
            broadcast_sync({
                "type": "message",
                "execution_id": execution_id,
                "sender": sender,
                "receiver": receiver,
                "content": content[:300],
                "message_type": message_type,
            })
        except Exception:
            pass

        return msg