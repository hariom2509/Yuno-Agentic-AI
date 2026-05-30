from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from app.db.database import Base


class Agent(Base):

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    description = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    model = Column(String, default="llama-3.3-70b-versatile")
    tools = Column(JSON, default=[])
    memory_enabled = Column(Boolean, default=True)
    max_iterations = Column(Integer, default=5)
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    channel = Column(String, default="none")  # none | telegram
    guardrails = Column(JSON, default={})  # {blocked_topics, max_output_length, ...}
    schedule_config = Column(JSON, default={})
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)