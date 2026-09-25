# 🤖 Yuno AI Agentic Orchestration Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-FF6F61?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![ReactFlow](https://img.shields.io/badge/ReactFlow-Visual_Builder-FF007A?style=flat-square&logo=react&logoColor=white)](https://reactflow.dev)
[![MCP Protocol](https://img.shields.io/badge/Model_Context_Protocol-JSON--RPC_2.0-0055FF?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A **production-grade, stateful multi-agent AI orchestration platform** built with Python, FastAPI, LangGraph, React, PostgreSQL, Redis, and Celery. Designed for enterprise deployments, it compiles visual **ReactFlow** node graphs into live **LangGraph StateGraphs** at runtime — featuring **Human-in-the-Loop (HITL)** approval workflows, **Just-In-Time (JIT) MCP tool scoping** for ~90% token reduction, a 3-tier capability security model with per-agent ACL enforcement, SHA-256 idempotency protection, and real-time execution observability via WebSockets and SSE.

<p align="center">
  <img src="docs/screenshots/01_dashboard.png" alt="Yuno AI Orchestration Platform Dashboard" width="100%" />
</p>

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Dynamic StateGraph Compilation** | Parses ReactFlow node/edge JSON at runtime and compiles it into an executable LangGraph `StateGraph(AgentState)` with conditional branching |
| **Multi-Agent Execution** | Sequential and conditional-branching multi-agent pipelines with per-node LLM model, tool, and system prompt assignment |
| **Human-in-the-Loop (HITL)** | LangGraph `interrupt()` pauses execution on destructive operations; operators approve or reject via Monitoring UI; resumes via `Command(resume=)` |
| **MCP Protocol Integration** | Full JSON-RPC 2.0 Model Context Protocol support over `stdio` and `http` transports — connects to any MCP-compliant tool server |
| **JIT MCP Tool Scoping** | `CapabilityRegistry` dynamically scopes tool schemas per prompt intent, reducing LLM context overhead by ~90% |
| **3-Tier Capability Security** | `BUILDER_VISIBLE` / `AGENT_ASSIGNABLE` / `PLATFORM_INTERNAL` exposure tiers with explicit Admin ACL enforcement via `agent_mcp_tools` junction table (least-privilege by default) |
| **Admin & Security Governance** | Dedicated Admin panel to configure tool exposure, risk levels (`LOW` to `CRITICAL`), HITL approval gates, server transports, and per-agent tool assignments |
| **SHA-256 Idempotency Guard** | Deterministic hash (`execution_id:node_id:tool_name`) prevents duplicate side-effecting tool calls across Celery retries |
| **Automated Failure Recovery** | Catches runtime exceptions, triggers GitHub issue creation via MCP, gated behind HITL approval |
| **Redis Conversational Memory** | Sliding 20-message window context per agent thread with 24h TTL and in-memory fallback |
| **Multi-Provider LLM Routing** | Unified OpenAI-compatible client routing across Groq (Llama 3.3 70B / 3.1 8B), OpenAI GPT-4o, and Google Gemini 2.5 Flash |
| **Input/Output Guardrails** | Configurable per-agent safety rules: blocked topics, max output length, JSON format enforcement, token budget cap |
| **Real-Time Observability** | WebSocket broadcast + SSE stream for sub-second live execution timeline, node transitions, and agent messages |
| **Token & Cost Tracking** | Per-execution token usage and USD cost computed and persisted to PostgreSQL after every LLM call |
| **Celery Distributed Task Queue** | Workflow executions offloaded to Celery workers backed by Redis broker for async, non-blocking operation |
| **Agent Scheduler** | Cron-based agent task scheduling with configurable intervals via `SchedulerService` |
| **Telegram Bot Gateway** | Agents receive and respond to messages via Telegram, with full execution context |
| **Workflow Templates** | Pre-built templates (Research & Analysis, Customer Support, Code Review, Data Pipeline) deployable in one click |
| **Custom Skills** | Python code snippets stored in DB, dynamically invoked as tools during agent execution |

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────┐
                    │   Telegram Gateway / Web UI       │
                    └─────────────────┬────────────────┘
                                      │
                          ┌───────────▼──────────┐
                          │  FastAPI Backend :8000 │
                          └───────────┬───────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                      ▼
          Celery Worker                      FastAPI BackgroundTasks
          (Redis Broker)                     (Async Execution)
                   └──────────────────┬──────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │    RuntimeEngine     │
                           │  ReactFlow → Graph   │
                           │  LangGraph Compile   │
                           └──────────┬──────────┘
              ┌───────────────────────┼──────────────────────┐
              ▼                       ▼                       ▼
        Input Guardrails        JIT Tool Scoping        LLM Layer
        (Safety Checks)        (90% Token Saving)   (Groq/OpenAI/Gemini)
                                      │
                           ┌──────────▼──────────┐
                           │  SHA-256 Idempotency │
                           │  Guard (Replay Safe) │
                           └──────────┬──────────┘
                                      │
                           ┌──────────▼──────────┐
                           │     MCP Layer        │
                           │  JSON-RPC 2.0        │
                           │  stdio / http        │
                           └──────────┬──────────┘
              ┌───────────────────────┼──────────────────────┐
              ▼                       ▼                       ▼
         yuno-tools            postgres-mcp             github-mcp
         (BUILDER_VISIBLE)     (AGENT_ASSIGNABLE)       (PLATFORM_INTERNAL)
                                      │
                           ┌──────────▼──────────┐
                           │  Persistence Layer   │
                           │  PostgreSQL / SQLite │
                           │  Redis Memory        │
                           │  WebSocket Broadcast │
                           └─────────────────────┘
```

---

## 🧠 Agentic AI Architecture Deep Dive

### 1. ReactFlow → LangGraph Compiler

The `RuntimeEngine` parses the workflow's ReactFlow JSON (`nodes`, `edges`) at runtime and compiles it into a live `StateGraph(AgentState)`:

- Each node becomes a typed graph node with its own LLM call, tool execution, and guardrail checks
- Edges with `condition` fields generate **conditional branching** via `add_conditional_edges()` based on substring evaluation of upstream node output
- The compiled graph is executed with a `thread_id`-isolated checkpointer for durable state

![Visual ReactFlow Multi-Agent Workflow Builder](docs/screenshots/02_visual_builder.png)

### 2. Human-in-the-Loop (HITL) Pause & Resume

```
Agent calls destructive tool
        │
        ▼
  interrupt(payload)           ← LangGraph saves checkpoint
        │
        ▼
  execution.status = "waiting_for_approval"
  execution.approval_data = {tool, node, message}
        │
        ▼
  Monitoring UI shows approval banner
        │
  Human clicks APPROVE / REJECT
        │
        ▼
  POST /executions/{id}/resume  { "decision": "APPROVED" }
        │
        ▼
  graph.invoke(Command(resume="APPROVED"), config)
        │
        ▼
  Execution continues from exact paused node
```

Hardcoded high-risk operations that always require approval: `drop_table`, `truncate_table`, `delete_repository`.

![Live Execution Monitoring with Interactive HITL Approval Gate](docs/screenshots/03_monitoring_hitl.png)

### 3. Model Context Protocol (MCP) Integration

Full JSON-RPC 2.0 MCP client supporting both `stdio` (subprocess) and `http` transports:

- `tools/list` — discovers and caches tool schemas into the `mcp_tools` DB table
- `tools/call` — executes tools with argument marshaling and result parsing
- **MCPToolAdapter** converts MCP schemas to OpenAI function-calling format for LLM tool binding
- **MCPAuthorizationService** enforces per-agent ACL: only tools explicitly granted via `agent_mcp_tools` junction table are callable

### 4. JIT Tool Scoping (Intent-Based Token Reduction)

Every agent invocation passes the task prompt through `CapabilityRegistry.classify_and_scope_tools()`:

```
Prompt: "List all tables in the database and show workflows"
        │
        ▼
  Keyword match: {"table", "database"} → DATABASE intent
        │
        ▼
  Load only postgres-mcp tool schemas  (~200 tokens)
  vs. loading ALL tools                (~2000+ tokens)
        │
        ▼
  ~90% token reduction per LLM call
```

### 5. SHA-256 Idempotency Guard

Before any side-effecting MCP tool runs, `IdempotencyGuard` computes:
```
key = SHA-256(f"{execution_id}:{node_id}:{tool_name}")
```
If the key was already executed (stored in Redis/memory), the call is skipped and the cached result returned — preventing duplicate DB writes, GitHub issues, or API charges on Celery retries.

### 6. Automated Failure Recovery Pipeline

```
Workflow execution raises exception
        │
        ▼
FailurePolicyService checks workflow_failure_policies table
        │
        ▼
Builds structured diagnostic payload:
  - Execution ID, failed node, stack trace, input task
        │
        ▼
Sets execution.status = "waiting_for_approval"
        │
        ▼
Human approves → github-mcp::create_issue posts structured
                 failure report to target repository
```

### 7. Autonomous Agent Management & Safety Guardrails

Configure specialized agent personas with granular model selection (Groq Llama 3.3 70B, OpenAI GPT-4o, Google Gemini Flash), system instructions, temperature, conversational memory, and strict input/output guardrails (blocked topics, max output length, JSON mode).

![Autonomous Agent Management & Guardrails](docs/screenshots/07_agents_management.png)

### 8. Production-Ready Multi-Agent Workflow Templates

Deploy complex multi-agent topologies in one click — including Research & Analysis, Customer Support, Code Review, and Data Pipeline workflows.

![One-Click Multi-Agent Workflow Templates](docs/screenshots/08_workflow_templates.png)

---

## 🗄️ Database Schema

**9 relational tables** (PostgreSQL in production, SQLite for local dev):

| Table | Purpose |
|---|---|
| `agents` | Agent personas, system prompts, temperature, model, memory toggle, guardrails config, scheduling |
| `workflows` | Workflow definitions with stored ReactFlow graph JSON (nodes, edges, positions) |
| `executions` | Execution logs with status, `thread_id`, `approval_data`, token usage, USD cost |
| `messages` | Chronological inter-agent and tool communication logs per execution |
| `skills` | Custom Python scripts stored as DB records and invoked as runtime tools |
| `mcp_servers` | MCP server registry — transport type, command, args, enabled state |
| `mcp_tools` | Cached tool definitions with `exposure`, `risk_level`, `requires_approval` classification |
| `agent_mcp_tools` | Junction table granting per-agent tool authorization (ACL) |
| `workflow_failure_policies` | Failure automation policies per workflow (action type, target repo, approval gate) |

---

## 🔒 3-Tier Capability Security & Governance Model

All MCP tools are classified and enforced across three exposure tiers:

| Tier | Visibility | Assignment Boundary | Example Tools |
|---|---|---|---|
| `BUILDER_VISIBLE` | Workflow canvas & tool nodes | Directly selectable by workflow designers | `web_search`, `calculator`, `report_generator`, `file_reader` |
| `AGENT_ASSIGNABLE` | Autonomous Agent nodes only | Explicitly assigned by Admin via `agent_mcp_tools` junction table | `postgres-mcp::execute_select`, `postgres-mcp::list_tables` |
| `PLATFORM_INTERNAL` | Runtime automation only | Never user-configurable; triggered by platform policies | `github-mcp::create_issue`, `github-mcp::delete_repository` |

### Least-Privilege Agent Creation & Runtime Enforcement

1. **Least-Privilege by Default**: Newly created agents start with zero external tool permissions.
2. **Administrative Authorization**: Administrators explicitly grant `AGENT_ASSIGNABLE` tools via the **Admin & Security** panel (`/admin`) or `POST /agents/{agent_id}/mcp-tools`.
3. **Builder Node Linking**: When designing workflows in the ReactFlow visual builder, selecting an agent node stores its database `agent_id` directly in the node configuration.
4. **Runtime ACL Verification**: When executing a tool call, `RuntimeEngine` resolves `agent_id` from node data and calls `MCPAuthorizationService.verify_agent_tool_access()`. If the tool is not in `agent_mcp_tools`, execution is immediately aborted with `MCPAuthorizationError`.
5. **Human-In-The-Loop Approval Gates**: Destructive operations (`drop_table`, `truncate_table`, `delete_repository`) and high-risk operations flagged with `requires_approval = True` automatically trigger `interrupt()` in LangGraph, pausing execution until approved or rejected via the Monitoring UI.
6. **Application-Level SQL SELECT Enforcement**: In addition to ACL checks, database MCP queries enforce strict read-only query semantics at the application layer.

### Admin & Security Governance Panel (`/admin`)

The dedicated **Admin** panel (`/admin`) provides centralized operational governance across capability exposures, agent permissions, and server health:

#### 1. MCP Tools 3-Tier Security & HITL Approval Gates
Real-time auditing and live configuration of tool exposure tiers (`BUILDER_VISIBLE`, `AGENT_ASSIGNABLE`, `PLATFORM_INTERNAL`), risk classifications (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and HITL approval flags via `PUT /api/mcp-servers/tools/{tool_id}`.

![Admin MCP Tools & 3-Tier Security](docs/screenshots/04_admin_tools_security.png)

#### 2. Granular Per-Agent Capability Authorization (ACL Manager)
Granular per-agent tool permission manager allowing operators to view granted capabilities, add tools via `POST /api/agents/{id}/mcp-tools`, or revoke access via `DELETE /api/agents/{id}/mcp-tools/{tool_name}`.

![Admin Agent Tool Permissions ACL](docs/screenshots/05_admin_agent_acls.png)

#### 3. MCP Server Registry & Transports
Live visibility into registered MCP servers, transport types (`stdio` vs. `http`), launch commands/endpoints, and server enablement toggles.

![Admin MCP Server Registry & Transports](docs/screenshots/06_admin_mcp_servers.png)


---

## ⚡ JIT MCP Tool Scoping

`CapabilityRegistry.classify_and_scope_tools()` routes task prompts to a single MCP server scope:

- **Database keywords** (`sql`, `table`, `query`, `schema`, `select`, ...) → `postgres-mcp` only
- **General tasks** → `yuno-tools` only

Prevents flooding the LLM context with all registered tool schemas — reduces prompt token overhead by ~90% per invocation.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** *(optional)*

---

### 1. Environment Setup

Copy `.env.example` to `backend/.env` and fill in your keys:

```bash
cp .env.example backend/.env
```

```env
# LLM Provider — at least one required
GROQ_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# LLM Base URL — set to Groq to use Llama 3 models (recommended free tier)
OPENAI_BASE_URL=https://api.groq.com/openai/v1

# Database — defaults to local SQLite if not set
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yuno_ai

# Redis — defaults to in-memory fallback if not set
REDIS_URL=redis://localhost:6379/0

# Integrations — optional
GITHUB_PERSONAL_ACCESS_TOKEN=
TELEGRAM_BOT_TOKEN=
```

> **Never commit your `.env` file.** It is listed in `.gitignore`.

---

### 2. Running Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API docs: **http://localhost:8000/docs**

**Frontend:**
```bash
cd frontend
npm install
npm start
```
- UI: **http://localhost:3000**

**Celery Worker** *(enables background task execution and distributed scheduling)*:
```bash
cd backend
celery -A app.tasks.celery_app:celery worker --loglevel=info --concurrency=2
```

---

### 3. Docker — Single Container *(Recommended for demos)*

Builds React frontend statically and serves everything from one FastAPI container:

```bash
# Windows
.\run_docker.ps1

# Linux / macOS
./run_docker.sh
```
- App: **http://localhost:8000**

---

### 4. Docker Compose — Full Distributed Stack

Runs FastAPI, React, PostgreSQL, Redis, and Celery Worker as separate containers:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Web UI | http://localhost:3001 |
| Backend API | http://localhost:8001 |

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

**19 tests — all passing.** Coverage includes:

- Agent CRUD operations & explicit least-privilege tool ACL assignment
- Workflow creation and template deployment
- RuntimeEngine graph & default workflow execution
- Guardrails input/output validation
- Calculator safe AST evaluation
- MCP server/tool registration and OpenAI adapter schema conversion
- MCP authorization and command allowlist security
- Tool executor MCP dispatch
- HITL failure policy and GitHub MCP integration

---

## 📁 Project Structure

```
yuno_full_platform/
├── Dockerfile                    # Unified multi-stage build (frontend + backend)
├── docker-compose.yml            # Full distributed stack
├── run_docker.ps1 / .sh          # One-click single-container deploy scripts
├── .env.example                  # Environment variable template
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point, router wiring, startup/shutdown
│   │   ├── db/
│   │   │   ├── database.py       # SQLAlchemy engine, session, DB URL resolution with fallback
│   │   │   └── migrations/       # Schema migration scripts
│   │   ├── models/               # SQLAlchemy ORM models (9 tables)
│   │   ├── schemas/              # Pydantic v2 request/response DTOs
│   │   ├── routes/               # REST API endpoints (agents, workflows, executions, MCP, skills, monitoring)
│   │   ├── runtime/
│   │   │   ├── runtime_engine.py # LangGraph StateGraph compiler & multi-agent executor
│   │   │   ├── checkpointer.py   # MemorySaver (dev) / PostgresSaver (prod)
│   │   │   ├── guardrails.py     # Per-agent input/output safety validation
│   │   │   ├── idempotency.py    # SHA-256 idempotency guard for side-effecting MCP tools
│   │   │   └── memory_manager.py # Redis-backed sliding window conversational memory
│   │   ├── services/
│   │   │   ├── capability_registry.py    # 3-tier security model & JIT tool scoping
│   │   │   ├── openai_service.py         # Multi-provider LLM client with cost tracking
│   │   │   ├── failure_policy_service.py # Automated failure → GitHub issue pipeline
│   │   │   └── scheduler_service.py      # Cron-based agent task scheduler
│   │   ├── mcp/
│   │   │   ├── client.py         # JSON-RPC 2.0 stdio/http MCP client
│   │   │   ├── manager.py        # MCP tool dispatch with ACL enforcement
│   │   │   ├── authorization.py  # Per-agent tool authorization verification
│   │   │   ├── adapter.py        # MCP schema → OpenAI function calling format adapter
│   │   │   └── servers/          # Native MCP stdio servers (yuno-tools, postgres-mcp)
│   │   ├── tasks/                # Celery app & workflow background task definitions
│   │   ├── tools/                # Native Python tools (web_search, calculator, report_generator)
│   │   ├── websocket/            # WebSocket connection manager & sync-to-async event bridge
│   │   └── static/               # Compiled React build (served in single-container mode)
│   ├── tests/                    # pytest integration & unit tests (19 tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # React Router layout & sidebar navigation
│   │   ├── pages/                # Dashboard, Agents, Workflows, Builder, Monitoring, Skills, Templates, Admin
│   │   ├── services/api.js       # Axios client with dynamic host resolution
│   │   └── styles/global.css     # Global design system
│   └── package.json
└── scripts/                      # Dev helper scripts
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.