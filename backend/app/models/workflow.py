from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from app.db.database import Base


class Workflow(Base):

    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    graph = Column(JSON, default={"nodes": [], "edges": []})
    template = Column(String, nullable=True)  # source template name if created from one
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)