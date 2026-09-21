# 🤖 Yuno AI Agentic Orchestration Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-FF6F61?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![ReactFlow](https://img.shields.io/badge/ReactFlow-Visual_Builder-FF007A?style=flat-square&logo=react&logoColor=white)](https://reactflow.dev)
[![MCP Protocol](https://img.shields.io/badge/Model_Context_Protocol-JSON--RPC_2.0-0055FF?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A **production-grade, stateful multi-agent AI orchestration platform** built with Python, FastAPI, LangGraph, React, PostgreSQL, Redis, and Celery. Designed for enterprise deployments, it compiles visual **ReactFlow** node graphs into live **LangGraph StateGraphs** at runtime — featuring **Human-in-the-Loop (HITL)** approval workflows, **Just-In-Time (JIT) MCP tool scoping** for ~90% token reduction, a 3-tier capability security model with per-agent ACL enforcement, SHA-256 idempotency protection, and real-time execution observability via WebSockets.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Visual Workflow Builder** | Drag-and-drop ReactFlow canvas that compiles directly into executable LangGraph `StateGraph` instances |
| **Multi-Agent Execution** | Sequential and conditional-branching multi-agent pipelines with per-node LLM & tool assignment |
| **Human-in-the-Loop (HITL)** | LangGraph `interrupt()` pauses execution on destructive operations; operators approve/reject via Monitoring UI |
| **JIT MCP Tool Scoping** | `CapabilityRegistry` inspects task prompts and dynamically scopes tool payloads — ~90% token reduction |
| **3-Tier Capability Security** | `BUILDER_VISIBLE` / `AGENT_ASSIGNABLE` / `PLATFORM_INTERNAL` exposure tiers enforced across all MCP tools |
| **SHA-256 Idempotency Guard** | Prevents duplicate execution of side-effecting tools across Celery retries |
| **Failure Recovery Pipeline** | Catches workflow failures and gates GitHub issue creation behind HITL approval |
| **Redis Conversational Memory** | Sliding 20-message window context per agent thread with 24h TTL and in-memory fallback |
| **Real-Time Observability** | WebSocket broadcast for sub-second live execution timeline in the Monitoring UI |
| **Token & Cost Tracking** | Per-execution token usage and USD cost logged to PostgreSQL |
| **Telegram Integration** | Agents can be triggered and respond directly via a Telegram bot |
| **Scheduler** | Cron-based agent task scheduling via `SchedulerService` |

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────┐
│    Telegram Gateway / Web UI        │
└──────────────────┬──────────────────┘
                   │
       ┌───────────▼───────────┐
       │  FastAPI Backend :8000 │
       └───────────┬───────────┘
                   │
     ┌─────────────┴─────────────┐
     ▼                           ▼
Celery Worker              FastAPI BackgroundTasks
     └─────────────┬─────────────┘
                   ▼
          ┌─────────────────┐
          │  RuntimeEngine  │
          │ ReactFlow→Graph │
          └────────┬────────┘
     ┌─────────────┼──────────────┐
     ▼             ▼              ▼
 Guardrails   JIT Scoping   LLM Layer
 (Safety)   (Token Savings) (Groq/OpenAI/Gemini)
                   │
          ┌────────▼────────┐
          │  MCP Layer      │
          │ JSON-RPC 2.0    │
          └────────┬────────┘
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
yuno-tools   postgres-mcp   github-mcp
(BUILDER)    (AGENT)        (PLATFORM)
```

---

## 🗄️ Database Schema

**8 relational tables** (PostgreSQL in production, SQLite for local dev):

| Table | Purpose |
|---|---|
| `agents` | Agent personas, system prompts, temperature, model, memory, guardrails, scheduling |
| `workflows` | Workflow definitions with stored ReactFlow graph JSON (nodes, edges, positions) |
| `executions` | Execution logs, status, `thread_id`, `approval_data`, token usage, cost |
| `messages` | Chronological inter-agent and tool communication logs |
| `skills` | Custom Python scripts executed at runtime |
| `mcp_servers` | MCP server registry (stdio/http transport, commands, args) |
| `mcp_tools` | Tool definitions classified by `exposure`, `risk_level`, `requires_approval` |
| `agent_mcp_tools` | Junction table for per-agent tool authorization (ACL) |
| `workflow_failure_policies` | Maps workflow failures to automated GitHub issue creation |

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

# LLM Base URL — set to Groq to use Llama models (default)
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

**Celery Worker** *(optional — enables background task execution)*:
```bash
cd backend
celery -A app.tasks.celery_app:celery worker --loglevel=info --concurrency=2
```

---

### 3. Docker — Single Container *(Recommended for demos)*

Builds the React frontend statically and serves everything from a single FastAPI container:

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

Covers agent CRUD, workflow execution, guardrails, MCP capability authorization, and the HITL approval flow — **18 tests, all passing**.

---

## 🔒 3-Tier Capability Security

All MCP tools are classified into one of three exposure tiers:

| Tier | Who Sees It | Example Tools |
|---|---|---|
| `BUILDER_VISIBLE` | Workflow canvas users | `web_search`, `calculator`, `report_generator` |
| `AGENT_ASSIGNABLE` | Explicitly authorized agents | `postgres-mcp` (query_database, list_tables) |
| `PLATFORM_INTERNAL` | Platform runtime only | `github-mcp` (create_issue, delete_repository) |

Destructive operations (`drop_table`, `truncate_table`, `delete_repository`) always trigger a `HITL interrupt()` requiring human approval before execution.

---

## ⚡ JIT MCP Tool Scoping

`CapabilityRegistry.classify_and_scope_tools()` inspects task prompts for domain keywords and scopes tool schemas to a single MCP server:

- **Database keywords** (`sql`, `table`, `query`, ...) → scopes to `postgres-mcp` only
- **General tasks** → scopes to `yuno-tools` only

This prevents flooding the LLM context with irrelevant tool schemas, reducing token overhead by ~90%.

---

## 📁 Project Structure

```
yuno_full_platform/
├── Dockerfile                    # Unified multi-stage build (frontend + backend)
├── docker-compose.yml            # Full distributed stack
├── run_docker.ps1 / .sh          # One-click single-container scripts
├── .env.example                  # Environment variable template
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point, router wiring, startup/shutdown
│   │   ├── db/
│   │   │   ├── database.py       # SQLAlchemy engine, session, DB URL resolution
│   │   │   └── migrations/       # Schema migration scripts
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response DTOs
│   │   ├── routes/               # REST API endpoints (agents, workflows, executions, MCP, monitoring)
│   │   ├── runtime/
│   │   │   ├── runtime_engine.py # LangGraph StateGraph compiler & executor
│   │   │   ├── checkpointer.py   # MemorySaver (dev) / PostgresSaver (prod — see comments)
│   │   │   ├── guardrails.py     # Input/output safety validation
│   │   │   ├── idempotency.py    # SHA-256 idempotency guard for MCP tools
│   │   │   └── memory_manager.py # Redis-backed conversational memory
│   │   ├── services/
│   │   │   ├── capability_registry.py    # 3-tier tool security & JIT scoping
│   │   │   ├── openai_service.py         # Multi-provider LLM client (Groq/OpenAI/Gemini)
│   │   │   ├── failure_policy_service.py # Automated failure → GitHub issue pipeline
│   │   │   └── scheduler_service.py      # Cron-based agent task scheduler
│   │   ├── mcp/
│   │   │   ├── client.py         # JSON-RPC 2.0 stdio/http client
│   │   │   ├── manager.py        # MCP tool dispatch with auth enforcement
│   │   │   ├── authorization.py  # Per-agent tool ACL verification
│   │   │   ├── adapter.py        # MCP schema → OpenAI function calling adapter
│   │   │   └── servers/          # Native MCP stdio servers (yuno-tools, postgres-mcp)
│   │   ├── tasks/                # Celery app & workflow background tasks
│   │   ├── tools/                # Native Python tools (web_search, calculator, report_generator)
│   │   ├── websocket/            # WebSocket connection manager & sync-to-async bridge
│   │   └── static/               # Compiled React build (served in single-container mode)
│   ├── tests/                    # pytest integration & unit tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # React Router layout & sidebar navigation
│   │   ├── pages/                # Dashboard, Agents, Workflows, Builder, Monitoring, Skills, Templates
│   │   ├── services/api.js       # Axios client with dynamic host resolution
│   │   └── styles/global.css     # Global design system
│   └── package.json
└── scripts/                      # Dev helper scripts
```

---

## 🔬 Framework Decision

| Framework | Decision | Reason |
|---|---|---|
| **LangGraph** | ✅ Selected | Explicit cyclic `StateGraph`, shared `AgentState`, native `interrupt()`/`Command(resume=)` checkpointing, deterministic conditional edge routing |
| **AutoGen / CrewAI** | ❌ Rejected | Non-deterministic conversational loops cause infinite reasoning cycles and uncontrolled API cost |
| **Custom Engine** | ❌ Rejected | High engineering overhead; requires re-implementing checkpointing, state serialization, and thread isolation from scratch |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.