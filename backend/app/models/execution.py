from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.db.database import Base


class Execution(Base):

    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, index=True)
    # status values: pending | running | completed | failed | waiting_for_approval
    status = Column(String, default="pending")
    current_node = Column(String)
    input_task = Column(Text)
    final_output = Column(Text)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # LangGraph Checkpointing & HITL fields
    # thread_id: LangGraph checkpoint thread key = str(execution.id).
    #   Used by builder.compile(checkpointer=...) to isolate per-execution state.
    #   Required to call graph.invoke(Command(resume=...), config) after HITL pause.
    thread_id = Column(String, nullable=True, index=True)

    # approval_data: JSON-serialized interrupt() payload.
    #   Stored when status transitions to "waiting_for_approval".
    #   Shape: {"status": "WAITING_FOR_APPROVAL", "node": "...", "tool": "...", "message": "..."}
    #   Displayed in the Monitoring UI to guide the human approver.
    approval_data = Column(Text, nullable=True)

    # MIGRATION NOTE (existing databases):
    #   SQLite:     ALTER TABLE executions ADD COLUMN thread_id TEXT;
    #               ALTER TABLE executions ADD COLUMN approval_data TEXT;
    #   PostgreSQL: alembic revision --autogenerate -m "add_hitl_columns"
    #               alembic upgrade head