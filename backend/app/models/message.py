from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from app.db.database import Base


class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, index=True)
    sender = Column(Text)
    receiver = Column(Text)
    content = Column(Text)
    message_type = Column(String, default="agent")  # human | agent | tool | system
    timestamp = Column(DateTime, default=datetime.utcnow)