# Graph Report - yuno_full_platform  (2026-09-25)

## Corpus Check
- Corpus is ~46,271 words - fits in a single context window. You may not need a graph.

## Summary
- 1499 nodes · 4415 edges · 78 communities (61 shown, 17 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 647 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Runtime Engine & Core Services
- React Frontend Bundle (Part A)
- React Frontend Bundle (Part B)
- MCP Adapter & Tool Protocol
- App Core & Database Layer
- MCP Native Server Tools
- React Frontend Bundle (Part C)
- React Frontend Bundle (Part D)
- React Frontend Bundle (Part E)
- MCP Registry & Session Mgmt
- React Frontend Bundle (Part F)
- React Frontend Bundle (Part G)
- Skills API Routes
- React Frontend Bundle (Part H)
- DB Migrations & Guardrails
- Agent Models & Routes
- React Frontend Bundle (Part I)
- React Frontend Bundle (Part J)
- React Frontend Bundle (Part K)
- React Frontend Bundle (Part L)
- Workflow Models & Routes
- React Frontend Bundle (Part M)
- React Frontend Bundle (Part N)
- React Frontend Bundle (Part O)
- LangGraph Patterns: HITL
- LangGraph Patterns: Basic Nodes
- Agent Service & Execution
- LangGraph Patterns: Tool Calling
- LangGraph Patterns: Conditional
- LangGraph Patterns: Subgraphs
- Celery Workers & Tasks
- Telegram Bot Integration
- LangGraph Patterns: Cross-Agent Mem
- LangGraph Patterns: Time Travel
- LangGraph Patterns: ReAct Agent
- LangGraph Patterns: Persistence
- LangGraph Patterns: Multi-Agent
- LangGraph Patterns: Deferred Node
- LangGraph Patterns: Dynamic Break
- LangGraph Patterns: Workflow Graph
- LangGraph Patterns: Map-Reduce
- LangGraph Patterns: Event Driven
- LangGraph Patterns: Error Recovery
- LangGraph Patterns: Command Route
- LangGraph Patterns: Supervisor
- LangGraph Patterns: Parallel Fanout
- App Lifecycle & Scheduler
- LangGraph Patterns: Reducers
- LangGraph Patterns: Handoff
- Test Fixtures & Conftest
- Frontend Package Dependencies
- WebSocket Connection Manager
- LangGraph Patterns: Durable Exec
- LangGraph Patterns: Streaming
- LangGraph Patterns: Memory Arch
- Frontend Agents Page
- Frontend Builder Page
- Frontend Dashboard & API Service
- React Frontend Bundle (Part P)
- Frontend Monitoring Page
- Frontend Skills Page
- Docker Compose Infrastructure
- Graphify Agent Config
- MCP Package Init
- Docker Run Scripts
- Bootstrap Scripts
- Backend Start Scripts
- Frontend Start Scripts
- Worker Start Scripts
- SQLAlchemy Dependency

## God Nodes (most connected - your core abstractions)
1. `730()` - 293 edges
2. `a()` - 81 edges
3. `n()` - 73 edges
4. `t()` - 60 edges
5. `r()` - 59 edges
6. `e()` - 57 edges
7. `u()` - 46 edges
8. `d()` - 45 edges
9. `i()` - 44 edges
10. `c()` - 41 edges

## Surprising Connections (you probably didn't know these)
- `create_hitl()` --uses--> `MCPToolRegistry`  [INFERRED]
  scripts/dev_patch_helpers/create_pending_hitl_execution.py → backend/app/mcp/registry.py
- `create_hitl()` --uses--> `MCPServer`  [INFERRED]
  scripts/dev_patch_helpers/create_pending_hitl_execution.py → backend/app/models/mcp_server.py
- `FastAPI Web Framework` --conceptually_related_to--> `Yuno AI Agentic Orchestration Platform`  [INFERRED]
  backend/requirements.txt → README.md
- `create_hitl()` --uses--> `Workflow`  [INFERRED]
  scripts/dev_patch_helpers/create_pending_hitl_execution.py → backend/app/models/workflow.py
- `create_hitl()` --uses--> `RuntimeEngine`  [INFERRED]
  scripts/dev_patch_helpers/create_pending_hitl_execution.py → backend/app/runtime/runtime_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Orchestration Stack** — readme_stategraph_compilation, readme_hitl, readme_celery_task_queue, backend_requirements_langgraph [INFERRED 0.85]
- **Security and Access Control** — readme_capability_security, readme_sha256_idempotency, readme_jit_mcp_scoping [INFERRED 0.75]

## Communities (78 total, 17 thin omitted)

### Community 0 - "Runtime Engine & Core Services"
Cohesion: 0.05
Nodes (67): Base, Workflow, deploy_template(), post, Session, create_workflow(), delete_workflow(), get_workflow() (+59 more)

### Community 1 - "React Frontend Bundle (Part A)"
Cohesion: 0.03
Nodes (59): bl(), Ea(), Go(), Hi(), Ri(), Vi(), zo(), Aa() (+51 more)

### Community 2 - "React Frontend Bundle (Part B)"
Cohesion: 0.04
Nodes (45): 730(), br(), cc(), Di(), dn(), dr(), ee(), eo() (+37 more)

### Community 3 - "MCP Adapter & Tool Protocol"
Cohesion: 0.08
Nodes (46): MCPToolAdapter, Any, Converts MCPTool DB record into OpenAI function representation: { "type":…, Adapts a list of MCPTool records into OpenAI function definitions., Adapts MCP Tool JSON-RPC definitions into standard OpenAI/LangChain tool…, MCPAuthorizationService, Session, Verifies that: 1. MCPServer exists and is enabled. 2. MCPTool exists on that… (+38 more)

### Community 4 - "App Core & Database Layer"
Cohesion: 0.08
Nodes (40): app_runtime_runtime_engine, app_services_capability_registry, asyncio, get_db(), health_check(), get, websocket, serve_spa() (+32 more)

### Community 5 - "MCP Native Server Tools"
Cohesion: 0.05
Nodes (34): ast, _analyze_text(), calculate(), _calculate_metrics(), _format_report(), generate_report(), handle_initialize(), handle_tools_call() (+26 more)

### Community 6 - "React Frontend Bundle (Part C)"
Cohesion: 0.10
Nodes (51): 234(), n(), P(), S(), T(), w(), z(), _e() (+43 more)

### Community 7 - "React Frontend Bundle (Part D)"
Cohesion: 0.08
Nodes (33): A(), b(), ja(), Oa(), c(), d(), f(), g() (+25 more)

### Community 8 - "React Frontend Bundle (Part E)"
Cohesion: 0.07
Nodes (39): c(), e(), Bi(), el(), jo(), n(), zi(), au() (+31 more)

### Community 9 - "MCP Registry & Session Mgmt"
Cohesion: 0.09
Nodes (36): Clears the session pool., MCPToolRegistry, Session, Connects to the target MCP server, sends `tools/list` JSON-RPC request,…, Retrieves all enabled MCP tools authorized for the specified agent_id. Returns…, authorize_agent_mcp_tools(), delete_mcp_server(), get_all_mcp_tools() (+28 more)

### Community 10 - "React Frontend Bundle (Part F)"
Cohesion: 0.18
Nodes (37): 330(), 717(), p(), ua(), ba(), bm(), c(), ca() (+29 more)

### Community 11 - "React Frontend Bundle (Part G)"
Cohesion: 0.10
Nodes (37): bt(), Ci(), Ec(), fc(), gc(), hc(), Nc(), Ni() (+29 more)

### Community 12 - "Skills API Routes"
Cohesion: 0.11
Nodes (26): create_skill(), delete_skill(), get_skills(), delete, get, post, put, Session (+18 more)

### Community 13 - "React Frontend Bundle (Part H)"
Cohesion: 0.09
Nodes (33): jc(), lu(), xs(), as(), brighter(), bs(), cu(), darker() (+25 more)

### Community 14 - "DB Migrations & Guardrails"
Cohesion: 0.09
Nodes (19): Safely adds capability classification columns and new policy tables if they do…, run_migrations(), wait_for_db(), Base, WorkflowFailurePolicy, GuardrailResult, Guardrails, Guardrails engine for agent input/output safety. Enforces configurable rules… (+11 more)

### Community 15 - "Agent Models & Routes"
Cohesion: 0.15
Nodes (23): Agent, Base, assign_agent_mcp_tools(), create_agent(), delete_agent(), get_agent(), get_agent_mcp_tools(), get_agents() (+15 more)

### Community 16 - "React Frontend Bundle (Part I)"
Cohesion: 0.11
Nodes (25): ae(), Ce(), es(), ie(), kl(), le(), Os(), re() (+17 more)

### Community 17 - "React Frontend Bundle (Part J)"
Cohesion: 0.09
Nodes (28): an(), c(), ca(), Cs(), Fa(), gl(), Gr(), ki() (+20 more)

### Community 18 - "React Frontend Bundle (Part K)"
Cohesion: 0.15
Nodes (26): Ao(), bc(), da(), Do(), gs(), Ic(), J(), Jl() (+18 more)

### Community 19 - "React Frontend Bundle (Part L)"
Cohesion: 0.10
Nodes (26): Cl(), ds(), Et(), fs(), hs(), js(), $l(), ls() (+18 more)

### Community 20 - "Workflow Models & Routes"
Cohesion: 0.13
Nodes (20): a(), ba(), bo(), fo(), ga(), kc(), sa(), U() (+12 more)

### Community 21 - "React Frontend Bundle (Part M)"
Cohesion: 0.14
Nodes (15): get_agent_assignable_tools(), get_builder_tools(), get_github_integration_status(), get, Session, Returns only BUILDER_VISIBLE capabilities grouped for the Visual Builder…, Returns AGENT_ASSIGNABLE tools eligible for Agent configuration., Reports runtime status for GitHub MCP platform integration without blocking… (+7 more)

### Community 22 - "React Frontend Bundle (Part N)"
Cohesion: 0.13
Nodes (16): 202(), j(), M(), N(), O(), P(), F(), af() (+8 more)

### Community 23 - "React Frontend Bundle (Part O)"
Cohesion: 0.23
Nodes (10): MCPClientSession, Any, Client session handling JSON-RPC 2.0 protocol exchanges over stdio or HTTP…, Sends `tools/list` JSON-RPC request to the MCP server., Sends `tools/call` JSON-RPC request to the MCP server., MCPConnectionError, MCPExecutionError, Raised when an MCP tool invocation returns an error or fails. (+2 more)

### Community 24 - "LangGraph Patterns: HITL"
Cohesion: 0.16
Nodes (15): LangGraph Checkpointer — Durable Execution State Development: MemorySaver (in-…, CheckpointState, TypedDict, Concept 06: Checkpointing & State Persistence in LangGraph Demonstrates: 1. In-…, step_one_node(), step_two_node(), test_memory_checkpointer(), build_persistent_chat_graph() (+7 more)

### Community 25 - "LangGraph Patterns: Basic Nodes"
Cohesion: 0.14
Nodes (18): Ei(), Gi(), I(), Mi(), Pi(), qi(), Ti(), ui() (+10 more)

### Community 26 - "Agent Service & Execution"
Cohesion: 0.17
Nodes (16): agent_decision_node(), build_hitl_mcp_graph(), HITLState, mcp_execution_node(), TypedDict, Concept 09: Human-in-the-Loop (HITL) with Interrupt for Dangerous MCP Tools…, test_hitl_mcp_approval(), build_retry_policy_graph() (+8 more)

### Community 27 - "LangGraph Patterns: Tool Calling"
Cohesion: 0.30
Nodes (16): _describe_table(), _drop_table(), _execute_select(), _get_connection(), handle_initialize(), handle_tools_call(), handle_tools_list(), _insert_row() (+8 more)

### Community 28 - "LangGraph Patterns: Conditional"
Cohesion: 0.19
Nodes (16): Execution, Base, get_execution(), get_executions(), get, post, Session, Serializes an Execution ORM object to a dict, including new HITL fields. (+8 more)

### Community 29 - "LangGraph Patterns: Subgraphs"
Cohesion: 0.12
Nodes (17): 153(), c(), o(), x(), 391(), 43(), 443(), 461() (+9 more)

### Community 30 - "Celery Workers & Tasks"
Cohesion: 0.14
Nodes (17): dc(), en(), He(), Lc(), nn(), qt(), t(), _t() (+9 more)

### Community 31 - "Telegram Bot Integration"
Cohesion: 0.22
Nodes (9): App(), root, TEMPLATE_ICONS, Templates(), Workflows(), frontend_src_styles_global, lucide-react, react (+1 more)

### Community 32 - "LangGraph Patterns: Cross-Agent Mem"
Cohesion: 0.21
Nodes (12): build_tool_loop_graph(), calculate_tax_func(), mock_agent_node(), ProductionToolNode, TypedDict, Concept 03: Tool-Calling Loops in LangGraph Demonstrates: 1. Custom ToolNode…, Calculates 10% tax on an amount., Inspects the last message for tool_calls. (+4 more)

### Community 33 - "LangGraph Patterns: Time Travel"
Cohesion: 0.23
Nodes (14): al(), dl(), Ho(), ml(), so(), Uo(), vl(), Fa() (+6 more)

### Community 34 - "LangGraph Patterns: ReAct Agent"
Cohesion: 0.32
Nodes (12): build_parent_graph(), build_research_subgraph(), call_research_subgraph_wrapper(), parent_final_report_node(), parent_input_node(), ParentState, TypedDict, Concept 10: Subgraphs & Nested Graph Composition in LangGraph Demonstrates… (+4 more)

### Community 35 - "LangGraph Patterns: Persistence"
Cohesion: 0.24
Nodes (12): build_idempotency_graph(), build_loop_graph(), compute_idempotency_key(), IdempotencyState, infinite_loop_node(), TypedDict, Concept 18: Idempotency Keys for Side-Effecting Tools & Recursion Circuit…, Computes deterministic SHA-256 idempotency key for side-effecting tools. (+4 more)

### Community 36 - "LangGraph Patterns: Multi-Agent"
Cohesion: 0.15
Nodes (12): browserslist, development, production, name, private, scripts, build, start (+4 more)

### Community 37 - "LangGraph Patterns: Deferred Node"
Cohesion: 0.23
Nodes (6): MemoryManager, Manages short-term and cross-execution memory for agents. Memory is stored in…, Append a message to the agent's conversation memory., Retrieve the agent's conversation history., Clear an agent's memory for a given context., Build a full message array for an OpenAI-compatible chat call, including memory…

### Community 38 - "LangGraph Patterns: Dynamic Break"
Cohesion: 0.32
Nodes (11): aggregator_node(), build_dynamic_send_graph(), continue_to_workers(), document_processor_worker(), DynamicSendState, map_dispatcher_node(), TypedDict, Concept 05: Dynamic Parallel Execution with Send API vs Static Parallelism… (+3 more)

### Community 39 - "LangGraph Patterns: Workflow Graph"
Cohesion: 0.30
Nodes (11): build_yuno_production_graph(), BaseModel, TypedDict, Concept 19: Full Production Yuno Runtime Integration Demonstrates the unified…, test_yuno_production_runtime(), yuno_classifier_node(), yuno_synthesizer_node(), yuno_tool_executor_node() (+3 more)

### Community 40 - "LangGraph Patterns: Map-Reduce"
Cohesion: 0.21
Nodes (12): FastAPI Web Framework, LangGraph Orchestration, 3-Tier Capability Security Model, Celery Distributed Task Queue, Human-in-the-Loop (HITL) Workflow, JIT MCP Tool Scoping, Multi-Provider LLM Routing, MCP Protocol (JSON-RPC 2.0) (+4 more)

### Community 41 - "LangGraph Patterns: Event Driven"
Cohesion: 0.29
Nodes (11): ai(), ii(), li(), se(), si(), di(), ei(), me() (+3 more)

### Community 42 - "LangGraph Patterns: Error Recovery"
Cohesion: 0.35
Nodes (10): build_deterministic_router_graph(), coding_branch_node(), deterministic_router_fn(), general_branch_node(), TypedDict, Concept 11: Router Pattern (Deterministic Router vs LLM Intent Router)…, Zero-latency rule classification., research_branch_node() (+2 more)

### Community 43 - "LangGraph Patterns: Command Route"
Cohesion: 0.36
Nodes (9): build_command_graph(), coder_node(), CommandState, intent_classifier_node(), TypedDict, Concept 04: Command Primitive for State Update & Routing in LangGraph…, researcher_node(), test_command_routing() (+1 more)

### Community 44 - "LangGraph Patterns: Supervisor"
Cohesion: 0.40
Nodes (9): build_supervisor_graph(), coder_worker_node(), TypedDict, Concept 12: Supervisor Multi-Agent Pattern Demonstrates central Supervisor…, researcher_worker_node(), supervisor_node(), supervisor_routing_fn(), SupervisorState (+1 more)

### Community 45 - "LangGraph Patterns: Parallel Fanout"
Cohesion: 0.40
Nodes (9): aggregator_node(), build_parallel_fanout_graph(), cost_branch_node(), FanOutState, performance_branch_node(), TypedDict, Concept 14: Parallel Fan-Out / Fan-In Aggregation Pattern Demonstrates static…, security_branch_node() (+1 more)

### Community 46 - "App Lifecycle & Scheduler"
Cohesion: 0.33
Nodes (6): shutdown(), startup(), Starts the periodic background scheduler task., Stops the periodic background scheduler task., SchedulerService, on_event

### Community 47 - "LangGraph Patterns: Reducers"
Cohesion: 0.42
Nodes (8): aggregator_node(), build_parallel_reducer_graph(), ParallelState, TypedDict, Concept 02: Reducers and Parallel State Updates in LangGraph Demonstrates: 1.…, test_parallel_reducers(), worker_a_node(), worker_b_node()

### Community 48 - "LangGraph Patterns: Handoff"
Cohesion: 0.42
Nodes (8): build_handoff_graph(), HandoffState, intake_agent_node(), TypedDict, Concept 13: Handoff Multi-Agent Pattern Demonstrates direct peer-to-peer agent…, specialist_agent_node(), test_handoff_pattern(), triage_agent_node()

### Community 49 - "Test Fixtures & Conftest"
Cohesion: 0.22
Nodes (7): client(), db_session(), mock_openai(), fixture, Create a fresh database for each test., Create a test client that uses the test database., Mock the OpenAI service to avoid actual API calls during tests.

### Community 50 - "Frontend Package Dependencies"
Cohesion: 0.22
Nodes (9): dependencies, axios, lucide-react, react, react-dom, react-hot-toast, react-router-dom, react-scripts (+1 more)

### Community 51 - "WebSocket Connection Manager"
Cohesion: 0.29
Nodes (3): AbstractEventLoop, ConnectionManager, WebSocket

### Community 52 - "LangGraph Patterns: Durable Exec"
Cohesion: 0.43
Nodes (7): build_durable_graph(), DurableState, node_one(), node_two(), TypedDict, Concept 08: Durable Execution Semantics & Crash Resumption in LangGraph…, test_durable_resumption()

### Community 53 - "LangGraph Patterns: Streaming"
Cohesion: 0.36
Nodes (7): build_stream_graph(), TypedDict, Concept 16: Token & Event Streaming in LangGraph (astream_events) Demonstrates…, streaming_agent_node(), StreamState, test_event_streaming(), langgraph_graph

### Community 54 - "LangGraph Patterns: Memory Arch"
Cohesion: 0.39
Nodes (7): build_memory_architecture_graph(), memory_agent_node(), MemoryArchitectureState, TypedDict, Concept 17: 5-Tier Production Memory Architecture in Yuno AI Demonstrates: 1.…, retrieve_semantic_memory(), test_5_tier_memory()

### Community 55 - "Frontend Agents Page"
Cohesion: 0.25
Nodes (6): Agents(), CHANNELS, DEFAULT_FORM, MODELS, POSTGRES_MCP_TOOLS, YUNO_TOOLS

### Community 56 - "Frontend Builder Page"
Cohesion: 0.29
Nodes (5): AgentNodeComponent(), Builder(), formatToolLabel(), NODE_PALETTE, nodeTypes

### Community 57 - "Frontend Dashboard & API Service"
Cohesion: 0.29
Nodes (3): Dashboard(), api, axios

### Community 58 - "React Frontend Bundle (Part P)"
Cohesion: 0.29
Nodes (3): Cr(), Nr(), zr

### Community 61 - "Frontend Skills Page"
Cohesion: 0.40
Nodes (3): DEFAULT_FORM, Skills(), react-hot-toast

### Community 63 - "Docker Compose Infrastructure"
Cohesion: 0.67
Nodes (3): PostgreSQL Service, Redis Service, Docker Compose Services

## Knowledge Gaps
- **44 isolated node(s):** `Config`, `Config`, `name`, `version`, `private` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 388 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `730()` connect `React Frontend Bundle (Part B)` to `React Frontend Bundle (Part A)`, `React Frontend Bundle (Part C)`, `React Frontend Bundle (Part D)`, `React Frontend Bundle (Part E)`, `React Frontend Bundle (Part F)`, `React Frontend Bundle (Part G)`, `React Frontend Bundle (Part H)`, `React Frontend Bundle (Part I)`, `React Frontend Bundle (Part J)`, `React Frontend Bundle (Part K)`, `React Frontend Bundle (Part L)`, `Workflow Models & Routes`, `React Frontend Bundle (Part N)`, `LangGraph Patterns: Basic Nodes`, `LangGraph Patterns: Subgraphs`, `Celery Workers & Tasks`, `LangGraph Patterns: Time Travel`, `LangGraph Patterns: Event Driven`, `React Frontend Bundle (Part P)`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `Agent` connect `Agent Models & Routes` to `Runtime Engine & Core Services`, `MCP Adapter & Tool Protocol`, `App Core & Database Layer`, `MCP Registry & Session Mgmt`, `App Lifecycle & Scheduler`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `Execution` connect `LangGraph Patterns: Conditional` to `Runtime Engine & Core Services`, `MCP Adapter & Tool Protocol`, `App Core & Database Layer`, `DB Migrations & Guardrails`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `730()` (e.g. with `Bi()` and `Ce()`) actually correct?**
  _`730()` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `a()` (e.g. with `e()` and `kr()`) actually correct?**
  _`a()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `n()` (e.g. with `N()` and `O()`) actually correct?**
  _`n()` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `t()` (e.g. with `fc()` and `gc()`) actually correct?**
  _`t()` has 20 INFERRED edges - model-reasoned connections that need verification._