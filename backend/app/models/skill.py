from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from app.db.database import Base


class Skill(Base):

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, default="")
    code = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
