from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.db.database import Base


class Execution(Base):

    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, index=True)
    status = Column(String, default="pending")   # pending | running | completed | failed
    current_node = Column(String)
    input_task = Column(Text)
    final_output = Column(Text)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)