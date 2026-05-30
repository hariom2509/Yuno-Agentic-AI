import asyncio
import logging
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.message import Message
from app.runtime.tool_executor import ToolExecutor
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


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
        Parses the workflow graph JSON, builds a LangGraph StateGraph,
        executes it, and persists results.
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

        # Record human → first node message
        RuntimeEngine._dispatch(db, execution.id, "Human", "Coordinator", task, "human")

        try:
            graph_def = workflow.graph or {}
            nodes = graph_def.get("nodes", [])
            edges = graph_def.get("edges", [])

            if not nodes:
                # Fallback: run the default 3-agent research workflow
                result = RuntimeEngine._run_default_workflow(db, execution, task)
            else:
                result = RuntimeEngine._run_graph_workflow(db, execution, task, nodes, edges)

            execution.status = "completed"
            execution.current_node = "Completed"
            execution.final_output = result["output"]
            execution.tokens_used = result["tokens"]
            execution.cost_usd = result["cost"]
            execution.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {e}")
            execution.status = "failed"
            execution.current_node = "Failed"
            execution.final_output = f"Execution failed: {str(e)}"
            execution.completed_at = datetime.utcnow()

        db.commit()

        # Broadcast via WebSocket (fire-and-forget)
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
            pass  # WebSocket broadcast is best-effort

        return execution

    @staticmethod
    def _run_default_workflow(db: Session, execution: Execution, task: str) -> dict:
        """
        Default 3-agent research → analysis → report pipeline.
        Used when no graph is configured.
        """
        total_tokens = 0
        total_cost = 0.0

        # Node 1: Research Agent
        execution.current_node = "Research Agent"
        db.commit()
        RuntimeEngine._dispatch(db, execution.id, "Coordinator", "Research Agent", task, "agent")

        research_data = ToolExecutor.execute("web_search", task, db)
        RuntimeEngine._dispatch(db, execution.id, "Research Agent", "Analysis Agent", research_data, "tool")

        # Node 2: Analysis Agent
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

        RuntimeEngine._dispatch(
            db, execution.id, "Analysis Agent", "Report Agent",
            analysis_result["content"], "agent"
        )

        # Node 3: Report Agent
        execution.current_node = "Report Agent"
        db.commit()

        from app.tools.report_generator_tool import generate_report
        final_report = generate_report(analysis_result["content"])

        RuntimeEngine._dispatch(db, execution.id, "Report Agent", "Human", final_report, "agent")

        return {
            "output": final_report,
            "tokens": total_tokens,
            "cost": total_cost,
        }

    @staticmethod
    def _run_graph_workflow(
        db: Session, execution: Execution, task: str, nodes: list, edges: list
    ) -> dict:
        """
        Executes a user-defined graph from ReactFlow node/edge definitions.
        Builds a LangGraph StateGraph dynamically with support for conditional routing.
        """
        total_tokens = 0
        total_cost = 0.0

        # Build adjacency map: source -> list of (target, condition)
        adjacency: dict[str, list[tuple[str, str]]] = {}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            cond = edge.get("data", {}).get("condition", "").lower() if edge.get("data") else ""
            if src and tgt:
                adjacency.setdefault(src, []).append((tgt, cond))

        # Find start node (no incoming edges)
        all_targets = {e.get("target") for e in edges}
        start_nodes = [n for n in nodes if n.get("id") not in all_targets]
        if not start_nodes:
            start_nodes = nodes[:1]

        node_map = {n["id"]: n for n in nodes}

        # Build LangGraph StateGraph
        builder = StateGraph(AgentState)
        
        from app.runtime.guardrails import Guardrails
        from app.runtime.memory_manager import memory

        # Register all nodes
        for node in nodes:
            node_id = node["id"]
            node_data = node.get("data", {})
            node_type = node_data.get("type", "agent")
            label = node_data.get("label", node_id)

            def make_node_fn(nid, ndata, nlabel, ntype):
                def node_fn(state: AgentState) -> AgentState:
                    nonlocal total_tokens, total_cost

                    execution.current_node = nlabel
                    db.commit()

                    current_input = state.get("current_output") or state.get("task", "")
                    
                    # 1. Guardrails Input Check
                    guardrails_config = ndata.get("guardrails", {})
                    input_check = Guardrails.check_input(current_input, guardrails_config)
                    if not input_check.passed:
                        current_input = f"System Error: {input_check.reason}"
                        RuntimeEngine._dispatch(
                            db, execution.id, "System", nlabel,
                            current_input, "system"
                        )

                    RuntimeEngine._dispatch(
                        db, execution.id, "System", nlabel,
                        f"Executing node: {nlabel}", "system"
                    )

                    if ntype == "tool":
                        tool_name = ndata.get("tool", "web_search")
                        output = ToolExecutor.execute(tool_name, current_input, db)
                        msg_type = "tool"
                    else:
                        # Agent node — call OpenAI
                        sys_prompt = ndata.get(
                            "system_prompt",
                            f"You are {nlabel}. Complete the given task thoughtfully."
                        )
                        model = ndata.get("model", "llama-3.1-8b-instant")
                        temperature = ndata.get("temperature", 0.7)
                        memory_enabled = ndata.get("memory_enabled", True)
                        
                        context_key = str(execution.id)
                        history = memory.recall(nlabel, context_key) if memory_enabled else []

                        result = OpenAIService.chat(
                            system_prompt=sys_prompt,
                            user_prompt=current_input,
                            model=model,
                            temperature=temperature,
                            messages_history=history,
                        )
                        output = result["content"]
                        total_tokens += result["total_tokens"]
                        total_cost += result["cost_usd"]
                        msg_type = "agent"
                        
                        if memory_enabled:
                            memory.store(nlabel, "user", current_input, context_key)
                            memory.store(nlabel, "assistant", output, context_key)

                    # 2. Guardrails Output Check
                    output_check = Guardrails.check_output(output, guardrails_config)
                    if not output_check.passed:
                        output = f"Output blocked: {output_check.reason}"
                    else:
                        output = output_check.filtered_content

                    next_nodes = adjacency.get(nid, [])
                    receiver = node_map.get(next_nodes[0][0], {}).get("data", {}).get("label", "Human") if next_nodes else "Human"

                    RuntimeEngine._dispatch(
                        db, execution.id, nlabel, receiver, output, msg_type
                    )

                    new_history = state.get("history", []) + [{"node": nlabel, "output": output}]

                    return {
                        **state,
                        "current_output": output,
                        "history": new_history,
                        "tokens_used": total_tokens,
                        "cost_usd": total_cost,
                    }
                return node_fn

            builder.add_node(node_id, make_node_fn(node_id, node_data, label, node_type))

        # Add edges
        start_id = start_nodes[0]["id"]
        builder.set_entry_point(start_id)

        for node in nodes:
            nid = node["id"]
            targets = adjacency.get(nid, [])
            if not targets:
                builder.add_edge(nid, END)
            elif len(targets) == 1 and not targets[0][1]:
                # Single unconditional edge
                builder.add_edge(nid, targets[0][0])
            else:
                # Conditional routing
                def make_routing_fn(t_list):
                    def route(state: AgentState):
                        output_lower = state.get("current_output", "").lower()
                        for target_id, condition in t_list:
                            if condition and condition in output_lower:
                                return target_id
                        return t_list[0][0]  # Fallback to first
                    return route
                
                route_map = {tgt: tgt for tgt, _ in targets}
                builder.add_conditional_edges(nid, make_routing_fn(targets), route_map)

        graph = builder.compile()

        initial_state: AgentState = {
            "task": task,
            "history": [],
            "current_output": task,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }

        # Enforce iteration limit (recursion_limit) across nodes
        max_iter = 10  # default fallback
        for node in nodes:
            node_max = node.get("data", {}).get("max_iterations")
            if node_max:
                try:
                    max_iter = max(max_iter, int(node_max))
                except (ValueError, TypeError):
                    pass

        # LangGraph recursion limit must accommodate nodes and tool invocations
        final_state = graph.invoke(initial_state, config={"recursion_limit": max_iter + 5})

        from app.tools.report_generator_tool import generate_report
        raw_output = final_state.get("current_output", "No output")
        if str(raw_output).startswith("# AI Analysis Report"):
            final_output = raw_output
        else:
            final_output = generate_report(raw_output)

        return {
            "output": final_output,
            "tokens": final_state.get("tokens_used", total_tokens),
            "cost": final_state.get("cost_usd", total_cost),
        }

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

        # Broadcast message via WebSocket
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