# 🤖 Yuno AI Agentic Orchestration Platform

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-FF6F61?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![ReactFlow](https://img.shields.io/badge/ReactFlow-Visual_Builder-FF007A?style=flat-square&logo=react&logoColor=white)](https://reactflow.dev)
[![MCP Protocol](https://img.shields.io/badge/Model_Context_Protocol-JSON--RPC_2.0-0055FF?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A production-grade, stateful **Agentic AI Orchestration Platform** built with **Python, FastAPI, LangGraph, React, PostgreSQL, Redis, and Celery**. It compiles visual **ReactFlow** node graphs into live **LangGraph StateGraphs** at runtime, featuring **Human-in-the-Loop (HITL)** approval workflows, **Just-In-Time (JIT) Model Context Protocol (MCP)** tool scoping, a 3-tier capability security model, and real-time execution observability via WebSockets and Server-Sent Events (SSE).

---

## 🏛️ System Architecture

```
                                    ┌─────────────────────────────────────────┐
                                    │    Telegram Gateway / Web Dashboard     │
                                    └────────────────────┬────────────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ FastAPI Backend (:8000) │
                                            └────────────┬────────────┘
                                                         │
                        ┌────────────────────────────────┴────────────────────────────────┐
                        ▼                                                                 ▼
      ┌───────────────────────────────────┐                             ┌───────────────────────────────────┐
      │  Celery Worker (Task Queue)       │                             │  FastAPI BackgroundTasks (Local)  │
      └─────────────────┬─────────────────┘                             └─────────────────┬─────────────────┘
                        │                                                                 │
                        └────────────────────────────────┬────────────────────────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ RuntimeEngine           │
                                            │ ReactFlow → StateGraph  │
                                            └────────────┬────────────┘
                                                         │
       ┌───────────────────────┬─────────────────────────┼─────────────────────────┬───────────────────────┐
       ▼                       ▼                         ▼                         ▼                       ▼
┌──────────────┐     ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐   ┌───────────────────┐
│ Input        │     │ JIT Tool Scoping  │     │ LLM Layer         │     │ SHA-256           │   │ Human-in-the-Loop │
│ Guardrails   │ ──► │ (90% token saving)│ ──► │ (Groq/OpenAI/     │ ──► │ Idempotency Guard │ ─►│ interrupt() /     │
│ (Safety)     │     │ (Intent Routing)  │     │  Gemini Flash)    │     │ (Replay Safety)   │   │ Command(resume=)  │
└──────────────┘     └───────────────────┘     └───────────────────┘     └───────────────────┘   └───────────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ MCP Integration Layer   │
                                            │ (JSON-RPC 2.0 / stdio)  │
                                            └────────────┬────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       ▼                                 ▼                                 ▼
             ┌───────────────────┐             ┌───────────────────┐             ┌───────────────────┐
             │ yuno-tools        │             │ postgres-mcp      │             │ github-mcp        │
             │ (BUILDER_VISIBLE) │             │ (AGENT_ASSIGNABLE)│             │ (PLATFORM_INT)    │
             └───────────────────┘             └───────────────────┘             └───────────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ Persistence & Observ.   │
                                            │ - PostgreSQL Audit Logs │
                                            │ - Redis Agent Memory    │
                                            │ - WebSocket Broadcast   │
                                            │ - SSE Message Stream    │
                                            └─────────────────────────┘
```

---

## ✨ Key Features & Architectural Innovations

### 1. 🔄 Dynamic StateGraph Compilation & Multi-Agent Execution
- **ReactFlow-to-LangGraph Compiler**: Compiles visual frontend graph definitions (`nodes` and `edges`) into live, executable LangGraph `StateGraph(AgentState)` instances at runtime.
- **Conditional Output-Based Routing**: Graph edges support conditional branching based on substring evaluations of upstream node outputs, enabling dynamic multi-path decision trees.
- **Multi-Provider LLM Routing**: Seamlessly routes prompts across **Groq (Llama 3.3 70B / Llama 3.1 8B)**, **OpenAI (GPT-4o)**, and **Google Gemini 2.5 Flash**, with automated schema sanitization for Gemini-compatible function definitions.

### 2. 🛡️ Human-in-the-Loop (HITL) & Durable Pause-Resume
- **Gated Execution**: Critical or destructive tool operations (`drop_table`, `truncate_table`, `delete_repository`) automatically trigger LangGraph `interrupt()`, saving thread checkpoints and pausing execution.
- **Monitoring UI Approval**: Execution status updates to `waiting_for_approval`, rendering an approval banner on the visual Monitoring UI.
- **Command Resume**: Human operators approve or reject executions, resuming the exact graph node via `graph.invoke(Command(resume=decision), config)`.

### 3. ⚡ Intent-Based Just-In-Time (JIT) MCP Tool Scoping
- **Zero-Latency Intent Classifier**: `CapabilityRegistry.classify_and_scope_tools()` inspects task prompts for domain keywords, dynamically scoping tool payloads to target MCP servers (e.g., `postgres-mcp` for DB queries vs. `yuno-tools` for general research).
- **90% Token Reduction**: Prevents flooding LLM system context with unnecessary schemas, reducing prompt overhead from thousands of tokens down to domain-specific definitions.

### 4. 🔒 3-Tier Capability Security Model & Agent ACL
- **Tiered Capability Exposure**:
  - `BUILDER_VISIBLE`: User-facing canvas tools (`web_search`, `calculator`, custom skills).
  - `AGENT_ASSIGNABLE`: External agent capabilities requiring explicit authorization (`postgres-mcp`).
  - `PLATFORM_INTERNAL`: Platform automation tools restricted from standard agent configuration (`github-mcp`).
- **Granular Authorization**: `AgentMCPTool` junction table enforces per-agent tool permissions verified via `MCPAuthorizationService`.
- **SHA-256 Idempotency Shield**: `IdempotencyGuard` generates deterministic hashes (`execution_id:node_id:tool_name`) to prevent duplicate execution of side-effecting tools.

### 5. 🚨 Automated Failure Recovery Pipeline
- **Automated Failure Interception**: `FailurePolicyService` catches workflow runtime exceptions and dispatches diagnostic failure payloads (Execution ID, failed node, stack trace).
- **GitHub Issue Integration**: Gated behind HITL approval, authorized operators can post structured failure issues directly to target GitHub repositories via `github-mcp`.

### 6. 📊 Real-Time Execution Observability & Memory
- **WebSocket & SSE Streaming**: Real-time event broadcasting over `/ws/executions` and Server-Sent Events `/executions/{id}/stream` for sub-second timeline visibility.
- **Redis Conversational Memory**: `MemoryManager` maintains sliding 20-message window context per agent thread with 24-hour TTL and graceful in-memory fallback.
- **Token & Cost Tracking**: Live token usage and USD cost tracking logged in PostgreSQL for every execution.

---

## 🗄️ Relational Database Schema (PostgreSQL / SQLite)

The platform utilizes **9 relational tables**:

```
                       ┌───────────────────┐
                       │      agents       │
                       └─────────┬─────────┘
                                 │ 1
                                 │
                                 │ N
                       ┌─────────┴─────────┐
                       │  agent_mcp_tools  │ (ACL Junction)
                       └─────────┬─────────┘
                                 │ N
                                 │
                                 │ 1
┌───────────────────┐  ┌─────────┴─────────┐
│    mcp_servers    │──┤     mcp_tools     │
└───────────────────┘ 1│N                  │
                       └───────────────────┘

┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│     workflows     │──┤    executions     │──┤     messages      │
└─────────┬─────────┘ 1│N                  │ 1│N                  │
          │            └─────────┬─────────┘  └───────────────────┘
          │ 1                    │ 1
          │                      │
          │ N                    │ 1
┌─────────┴─────────┐  ┌─────────┴─────────┐  ┌───────────────────┐
│  failure_policies │  │      skills       │  │     templates     │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

1. **`agents`**: Agent personas, system prompts, temperature, model selection, memory toggles, guardrails, and scheduling JSON.
2. **`workflows`**: Workflow definitions with stored ReactFlow `graph` JSON (nodes, edges, positions).
3. **`executions`**: Execution logs, status (`running`, `completed`, `failed`, `waiting_for_approval`), `thread_id`, `approval_data`, token usage, and cost tracking.
4. **`messages`**: Chronological inter-agent and agent-tool communication logs linked to executions.
5. **`skills`**: Custom executable Python scripts dynamically evaluated at runtime via `exec()`.
6. **`mcp_servers`**: MCP server registry (`stdio`/`http` transport, commands, args, secret references, classification category).
7. **`mcp_tools`**: Cached tool definitions discovered from MCP servers via JSON-RPC 2.0 (`tools/list`), classified by `exposure`, `risk_level`, and `requires_approval`.
8. **`agent_mcp_tools`**: Junction table granting explicit agent-level access to assignable MCP tools.
9. **`workflow_failure_policies`**: Automation policies linking workflow failures to diagnostic GitHub issue generation.

---

## 🔬 AI Orchestration Framework Decision

| Evaluated Framework | Decision | Justification |
|---|---|---|
| **LangGraph** | **SELECTED** | Provides explicit, cyclic StateGraph definitions, shared state schema (`AgentState`), native interrupt/resume checkpointing, and predictable conditional edge routing required for enterprise compliance. |
| **AutoGen / CrewAI** | **REJECTED** | Conversational turn-taking in AutoGen/CrewAI relies on non-deterministic LLM loops that frequently suffer from infinite reasoning loops, driving up API costs and breaking strict DAG flow execution. |
| **Custom Execution Engine** | **REJECTED** | Rolling a custom runtime increases engineering overhead, lacks standard graph visualization tools, and requires re-implementing state serialization, checkpointing, and thread isolation. |

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (for frontend development)
- **Docker & Docker Compose**: (Optional, for full stack containerized deployment)

### 1. Environment Setup

Create a `.env` file in `backend/` (or copy `.env.example`):

```bash
# LLM Provider Keys (at least one required)
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Infrastructure (Optional: Defaults to local SQLite & in-memory fallbacks)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/yuno_ai
REDIS_URL=redis://localhost:6379/0

# Integration Keys (Optional)
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
TELEGRAM_BOT_TOKEN=...
```

---

### 2. Running Locally (Development Mode)

#### Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Documentation: **http://localhost:8000/docs**

#### Frontend (React)
```bash
cd frontend
npm install
npm start
```
- Web Application UI: **http://localhost:3000**

---

### 3. Running with Docker Compose (Full Distributed Stack)

Launch the complete stack (FastAPI Backend, React Frontend, PostgreSQL, Redis, Celery Worker):

```bash
docker-compose up --build
```
- **Web UI**: `http://localhost:3001`
- **Backend API**: `http://localhost:8001`

---

## 🧪 Testing

Run the automated test suite covering unit, integration, and MCP capability tests:

```bash
cd backend
pytest tests/ -v
```

---

## 📁 Repository Structure

```
yuno_full_platform/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI application entry point & router wiring
│   │   ├── db/                   # Database session management & schema migrations
│   │   ├── models/               # SQLAlchemy ORM models (agents, workflows, executions, MCP)
│   │   ├── routes/               # REST API endpoints (agents, workflows, executions, monitoring, MCP)
│   │   ├── runtime/              # LangGraph RuntimeEngine, checkpointer, guardrails, idempotency
│   │   ├── services/             # CapabilityRegistry, OpenAIService, FailurePolicyService, Scheduler
│   │   ├── mcp/                  # MCP Client, Manager, Registry, Adapter, & Servers
│   │   │   └── servers/          # Genuine MCP stdio servers (yuno-tools, postgres-mcp)
│   │   ├── tasks/                # Celery application & workflow background tasks
│   │   ├── tools/                # Native Python tools (web_search, calculator, report_generator)
│   │   └── websocket/            # WebSocket connection manager & sync-to-async event bridge
│   ├── tests/                    # Automated integration & unit test suite
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # React router & main workspace layout
│   │   ├── pages/                # Builder, Monitoring, Agents, Workflows, Skills, Templates
│   │   └── services/             # Axios API client with dynamic host resolution
│   └── package.json              # React dependencies
├── scripts/                      # Deployment & maintenance scripts
├── docker-compose.yml            # Multi-container stack orchestration
└── README.md                     # Technical reference & documentation
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.