from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from app.db.database import Base


class WorkflowFailurePolicy(Base):
    __tablename__ = "workflow_failure_policies"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    action_type = Column(String, default="CREATE_GITHUB_ISSUE")
    mcp_server_name = Column(String, default="github-mcp")
    repository_config = Column(JSON, default={"repo": "hariom2509/Yuno-Agentic-AI"})
    requires_approval = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
