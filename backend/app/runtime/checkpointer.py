"""
LangGraph Checkpointer — Durable Execution State

Development:  MemorySaver  (in-process, cleared on server restart)
Production:   PostgresSaver (durable across restarts, supports real HITL)

What checkpointing enables:
  1. Durable execution  — crash-recovery from last completed node
  2. HITL pause/resume  — graph.invoke(Command(resume=...)) on a saved thread
  3. State history      — graph.get_state_history(config) for debugging
  4. Thread isolation   — each execution_id is a separate thread in the checkpointer

Upgrade path (production):
  pip install langgraph-checkpoint-postgres
  Uncomment the PostgresSaver block below and set DATABASE_URL in .env
"""
import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# DEVELOPMENT CHECKPOINTER: MemorySaver
# In-process dict — supports HITL within one process lifetime.
# All checkpoints lost on server restart.
# ----------------------------------------------------------------
checkpointer = MemorySaver()
logger.info("LangGraph checkpointer initialized: MemorySaver (dev mode)")

# ----------------------------------------------------------------
# PRODUCTION UPGRADE — uncomment when ready:
# ----------------------------------------------------------------
# import os, psycopg2
# from langgraph.checkpoint.postgres import PostgresSaver
#
# _db_url = os.getenv("DATABASE_URL", "")
# if _db_url and not _db_url.startswith("sqlite"):
#     _conn = psycopg2.connect(_db_url)
#     checkpointer = PostgresSaver(_conn)
#     checkpointer.setup()   # idempotent: creates checkpoint tables if absent
#     logger.info("LangGraph checkpointer initialized: PostgresSaver (production)")
# else:
#     checkpointer = MemorySaver()
#     logger.info("LangGraph checkpointer initialized: MemorySaver (no postgres)")
