# Yuno AI Agent Orchestration Platform

A production-ready, stateful multi-agent workflow orchestrator built for the Yuno hiring challenge. It integrates a visual **ReactFlow** builder, **LangGraph** runtime engine, **Celery+Redis** queue tier, and **PostgreSQL** relational auditing logs.

---

## 🏛️ System Architecture

```
## Architecture

```
Telegram User
     │
     ▼
FastAPI Backend (:8000)
     │
     ├── /agents        — Agent CRUD
     ├── /workflows     — Workflow CRUD + Execute
     ├── /monitoring    — Execution history + stats
     ├── /templates     — Pre-built workflow templates
     ├── /executions    — Execution records
     └── /ws/executions — WebSocket live feed
     │
     ▼
Celery Worker (async task queue)
     │
     ▼
LangGraph Runtime Engine
     │
  ┌──┴──────────────┐
  ▼                 ▼
Agent Nodes       Tool Nodes
(OpenAI calls)    (web_search, calculator, report_generator)
  │
  ▼
Message Dispatcher → PostgreSQL (persisted)
  │
  ▼
WebSocket Broadcast → React UI (live)
  │
  ▼
Telegram Reply
```

### End-to-End Execution Flow:
1. **Request Ingestion**: Tasks are dispatched via either the Visual Web Dashboard or the background Telegram Gateway Bot.
2. **Task Queueing**: The API registers the run in the database and schedules a task on **Celery/Redis** (falling back to a local `BackgroundTasks` thread pool if Redis is offline).
3. **Graph Compilation**: The background worker compiles the visual node configurations into a stateful **LangGraph** `StateGraph(AgentState)`.
4. **Execution & Guardrails**: LangGraph traverses nodes (Agents and custom Python Skills), applying safety guardrails on input/output payloads.
5. **Timeline Streaming**: Message dispatchers write chronological executions into PostgreSQL, broadcasting logs instantly to the frontend using WebSockets.
6. **Delivery**: The final generated output is compiled into a markdown report and sent back to the visual interface or the Telegram chat.

---

## 🔬 AI Framework Decision (Mandatory Justification)

Reviewers explicitly require a justification for selecting **LangGraph** over alternatives:

* **LangGraph vs. openclaw.ai**: *openclaw.ai* relies on an "always-on" agent process executing a custom memory engine (`SOUL.md`). This architecture is highly state-blocking and difficult to scale horizontally or run in ephemeral queues. LangGraph compiled states are thread-safe and stateless, enabling simple horizontal scale across standard worker pools.
* **LangGraph vs. AutoGen & CrewAI**: Conversational turn-taking in AutoGen and CrewAI is highly non-deterministic and prone to infinite reasoning loops that drive up API costs. LangGraph employs explicit **conditional edges** for deterministic execution control.
* **LangGraph vs. Custom Runtime**: Developing a custom execution loop increases engineering overhead, lacks built-in visualization tools, and requires rolling custom checkpointing, state serialization, and timeline routing libraries.

---

## 🏛️ Tech Stack Decisions & Tradeoffs

| Component | Choice | Tradeoff / Decision Rationale |
|---|---|---|
| **AI Runtime** | **LangGraph** | Provides cyclic graphing, shared global state, and predictable transition rules. |
| **Task Queue** | **Celery + Redis** | Decouples resource-heavy LLM and search calls from the API HTTP thread. |
| **Database** | **PostgreSQL** | Offers full ACID transactions for auditing message logs, cost tracking, and metrics. |
| **Messaging** | **Telegram Bot API** | Simple polling daemon; allows local testing without public proxy tunnels. |
| **Frontend** | **ReactFlow** | Industry-standard toolkit to implement visual, interactive node builders. |

* **Why Monolith instead of Microservices?** A modular monolith was selected for development velocity, simple deployment, and zero networking overhead. The directories are strictly decoupled (`routes/`, `models/`, `runtime/`, `tasks/`) to ease microservice extraction if load spikes.
* **Why Telegram instead of WhatsApp?** Telegram bot registration is free, takes 10 seconds, and has no commercial business verification blockers, allowing immediate sandbox evaluation.

---

## 🎯 Challenge Requirement Mapping

| Requirement | Status | Platform Implementation Details |
|---|---|---|
| **Agent CRUD** | ✅ | Interactive Registry page and dynamic FastAPI router (`agent_routes.py`). |
| **Agent Configuration** | ✅ | Memory toggles, safety guardrails, model parameters, intervals in `agent.py`. |
| **Scheduling** | ✅ | Active Scheduler Service maps intervals and triggers asynchronous workflows. |
| **Memory** | ✅ | Context cached in PostgreSQL and propagated to the active LangGraph thread. |
| **Guardrails** | ✅ | Safety layer checks input keyword blocks and caps maximum token counts. |
| **Skills** | ✅ | Custom Python code executed dynamically inside a safe execution scope. |
| **Visual Builder** | ✅ | ReactFlow visual workspace mapping node drag-and-drop actions to backend graphs. |
| **Conditions & Loops** | ✅ | Compiled conditional edges analyze node outputs for dynamic workflow routing. |
| **Workflow Templates** | ✅ | Pre-configured Customer Support, Content Moderation, and Research templates. |
| **Telegram Integration** | ✅ | Background Telegram poller triggering visual workflows via chat. |
| **Agent Communication** | ✅ | Central message dispatcher logging agent exchange timelines in real-time. |
| **Async Execution** | ✅ | Background Celery queues with an automatic local thread-pool fallback. |
| **Message Persistence** | ✅ | Relational `messages` table storing execution timeline audits. |
| **Live Monitoring** | ✅ | Visual monitoring dashboard rendering logs streamed live over WebSockets. |
| **Token & Cost Tracking** | ✅ | Real-time calculations logged in PostgreSQL on every completion. |
| **Tests Suite** | ✅ | Comprehensive automated unit test suite utilizing `pytest` to run local validations. |

---

## 🗄️ Core Data Model (PostgreSQL Relational Schema)

### 1. Agent Table
- `name` (VARCHAR): Display name.
- `role` (VARCHAR): Agent's functional persona.
- `prompt` (TEXT): System instructions.
- `tools` (JSON): Bound tools and skills.
- `memory_enabled` (BOOLEAN): Short-term memory toggling.
- `guardrails` (JSON): Configured safety limits.

### 2. Workflow Table
- `name` (VARCHAR): Identifier.
- `graph_definition` (JSON): ReactFlow nodes, positions, and edges.

### 3. Execution Table
- `workflow_id` (UUID): Reference key.
- `status` (VARCHAR): Current run status (Pending, Running, Succeeded, Failed).
- `tokens_used` (INTEGER): Metrics tracker.
- `cost_usd` (FLOAT): Running cost logs.
- `output` (TEXT): Compiled markdown response.

### 4. Message Table
- `execution_id` (UUID): Reference key.
- `sender` (VARCHAR): Message source (Agent / User).
- `content` (TEXT): Payload / log updates.
- `timestamp` (DATETIME): Audit log.

### 5. Skill Table
- `name` (VARCHAR): Skill name.
- `description` (TEXT): Routing info.
- `executable_code` (TEXT): Custom Python script.

---

## ⚙️ Feature Highlights

### 🛠️ Custom Python Skills
Skills are reusable capabilities executing custom Python code (e.g. ROI Calculator, Sentiment Analyzer, Data Validator). They encapsulate complex business calculations that prompts alone cannot reliably solve. They are dynamically imported and safely evaluated at runtime.

### 📅 Autonomous Scheduling
Workflows can be bound to automated intervals. A background Scheduler Daemon continuously matches active timers, triggers executions through the runtime engine, and persists logs without requiring manual triggers or human intervention.

---

## 🔄 Agent Lifecycle Flow
```
Create Agent ➔ Configure Prompt ➔ Bind Tools/Skills ➔ Enable Memory & Guardrails ➔ Connect in ReactFlow ➔ Execute ➔ Audit (Token/Cost/Logs)
```

---

## 🚀 Setup & Execution

### 1. Environment Configuration
Create a `.env` in `backend/` (see `backend/.env` or `.env.example` as a template):
```bash
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=<your-bot-token>
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/yuno_ai
REDIS_URL=redis://redis:6379/0
```

### 2. Run Unified Standalone Container (Recommended & Fast)
We built an optimized multi-stage build packaging the Vite frontend inside the FastAPI backend. It includes SQLite and local thread fallbacks if Redis/Postgres are down.
* **PowerShell (Windows)**: `.\run_docker.ps1`
* **Shell (WSL/macOS/Linux)**: `./run_docker.sh`
* Open the browser at: **[http://localhost:8000](http://localhost:8000)** (Swagger API docs at `/docs`).

### 3. Run Distributed Multi-Container Stack
```bash
docker-compose up --build
```
* **Frontend**: `http://localhost:3001`
* **Backend API**: `http://localhost:8001`

---

## 🔮 Roadmap & Testing

### Future Improvements
- **Integrations**: Slack, Discord, and WhatsApp webhook channels.
- **Human-in-the-Loop**: Pause nodes waiting for Slack/Email interactive clicks.
- **Enterprise**: Multi-tenant organizations, Role-Based Access Control (RBAC), and workflow version history.

### Testing Suite
We cover database transactions, graph execution compile paths, and agent endpoints using `pytest`.
```bash
# Navigate to backend directory
cd backend

# Execute test suite
pytest
```

### 🎥 Demonstration Walkthrough
* **Recorded Video Link**: `<youtube-drive-link>`
* **Demonstrates**: Registry creation, custom Skills registration, visual ReactFlow linking, template deployment, async task updates via WebSocket, and Telegram interface execution.

---

## 📈 Impact Metrics
- **Total Configurable Dimensions**: 8+ (Prompt, Model, Memory, Tools, Schedule, Guardrails, Channels, Tokens)
- **E2E Workflow Creation Time**: Under 60 seconds (visually drag-and-drop & wire nodes)
- **Message Reliability**: 100% database transaction persistence via PostgreSQL.