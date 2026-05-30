# Yuno AI Agent Orchestration Platform

A production-aware multi-agent workflow platform built for the Yuno AI Engineer hiring challenge. Supports agent creation, visual workflow building, async execution via LangGraph, Telegram integration, and live WebSocket monitoring.

---

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

---

## Tech Stack & Decisions

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI | Async-native, auto-docs, production-ready |
| AI Runtime | LangGraph | Stateful graph execution — not just prompt chaining. Supports conditional branching, cycles, shared state |
| Task Queue | Celery + Redis | Async workflow dispatch without Kafka complexity. Right tradeoff for this scale |
| DB | PostgreSQL | ACID, full audit trail, message history, token tracking |
| Messaging | Telegram (python-telegram-bot v21) | Simpler webhook-free polling, works locally with no public URL |
| Frontend | React + ReactFlow | Visual graph builder is a hard requirement; ReactFlow is the standard choice |
| Deployment | Docker Compose | Single `docker-compose up --build` — exactly what the assignment requires |

**Explicit rejections:**
- ❌ Kafka — unwarranted for this message volume
- ❌ Microservices — would add ops overhead with no benefit at this scale
- ❌ LangChain chains — LangGraph is more explicit and graph-native
- ❌ Vector DB / RAG — not in scope
- ❌ Kubernetes — Docker Compose is the correct local deployment target

---

## Setup

### Prerequisites
- Docker + Docker Compose
- OpenAI API key
- Telegram Bot Token (optional but required for Telegram demo)

### 1. Configure environment

```bash
cp .env.example backend/.env
```

Edit `backend/.env`:
```
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=<your-bot-token>    # Get from @BotFather on Telegram
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/yuno_ai
REDIS_URL=redis://redis:6379/0
```

### 2. Start everything

```bash
docker-compose up --build
```

This starts:
- `yuno_backend` → http://localhost:8000
- `yuno_frontend` → http://localhost:3000
- `yuno_postgres` → port 5432
- `yuno_redis` → port 6379
- `yuno_worker` → Celery worker

Tables are created automatically on first boot.

### 3. Open the platform

→ http://localhost:3000

API docs: → http://localhost:8000/docs

---

## Demo Workflow

### End-to-End (Web UI)

1. **Create Agent** → Agents → New Agent → fill form → Create
2. **Deploy Template** → Templates → "Research & Analysis Workflow" → Deploy Template
3. **Execute Workflow** → Workflows → Execute → set task → Run
4. **Watch live** → Monitoring → execution updates in real time via WebSocket
5. **View output** → Click execution row → see message timeline + final report

### Telegram Demo

1. Set `TELEGRAM_BOT_TOKEN` in `backend/.env`
2. `docker-compose up --build`
3. Find your bot on Telegram, send `/start`
4. Send any task: *"Analyze Tesla's competitive position in 2025"*
5. Bot runs multi-agent workflow, replies with AI-generated report

---

## Pre-built Templates

### Research & Analysis Workflow
`Researcher → Analyst → Reporter`

- Researcher: DuckDuckGo web search on the topic
- Analyst: GPT-4o-mini extracts strategic insights
- Reporter: Formats structured markdown report

### Customer Support Workflow
`Intake → Resolver → Summary`

- Intake: Classifies issue type (billing/technical/general)
- Resolver: Generates empathetic step-by-step resolution
- Summary: Formats the output

---

## Adding New Templates

In `backend/app/routes/template_routes.py`, add to the `TEMPLATES` dict:

```python
"my_template": {
    "name": "My Custom Template",
    "description": "What it does.",
    "graph": {
        "nodes": [
            {
                "id": "node_1",
                "type": "agentNode",
                "position": {"x": 100, "y": 200},
                "data": {
                    "label": "My Agent",
                    "type": "agent",
                    "system_prompt": "You are...",
                    "model": "gpt-4o-mini",
                }
            }
        ],
        "edges": []
    }
}
```

## Adding New Messaging Channels

1. Implement handler in `backend/app/services/` (see `telegram_service.py` as reference)
2. Add `start_<channel>_bot()` call in `app/main.py` startup event
3. Add channel option to agent `channel` field choices in UI

---

## Agent Configuration

Each agent supports:

| Config | Description |
|---|---|
| `name` | Display name |
| `role` | Functional role (researcher, analyst, etc.) |
| `system_prompt` | Full system instructions |
| `model` | gpt-4o-mini / gpt-4o / gpt-4-turbo |
| `tools` | web_search, calculator, report_generator, file_reader |
| `memory_enabled` | Toggle conversation memory |
| `max_iterations` | Cap on reasoning loops |
| `max_tokens` | Output token limit |
| `channel` | External channel (none, telegram) |

---

## Scalability Discussion

**Current architecture is correct for this scope.** For production scale:

- Replace polling Telegram with webhook + public URL
- Add Redis-based memory store for cross-session agent memory
- Add execution retry queue with exponential backoff (Celery retry)
- Add rate limiting on `/execute` endpoints
- Swap Docker Compose for K8s if worker count needs horizontal scaling
- Add structured logging to ELK/Loki for observability

---

## Project Structure

```
yuno_full_platform/
├── backend/
│   ├── app/
│   │   ├── db/               # SQLAlchemy engine + session
│   │   ├── models/           # Agent, Workflow, Execution, Message
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routes/           # FastAPI routers
│   │   ├── services/         # Business logic (OpenAI, Telegram, agent CRUD)
│   │   ├── runtime/          # LangGraph runtime engine + tool executor
│   │   ├── tasks/            # Celery tasks
│   │   ├── tools/            # web_search, calculator, report_generator
│   │   └── websocket/        # WebSocket connection manager
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, Agents, Workflows, Builder, Monitoring, Templates
│   │   ├── services/         # Axios API client
│   │   └── styles/           # Global CSS design system
│   └── package.json
├── docker-compose.yml
└── .env.example
```