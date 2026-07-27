from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    transport = Column(String, nullable=False, default="stdio")  # stdio | http
    command = Column(String, nullable=True)  # Command for stdio, e.g. "npx" or "python"
    args = Column(JSON, default=[])  # Command arguments for stdio
    url = Column(String, nullable=True)  # Server endpoint URL for http transport
    secret_reference = Column(String, nullable=True)  # Key or secret reference identifier
    env_vars = Column(JSON, default={})  # Non-sensitive env vars or config overrides
    enabled = Column(Boolean, default=True)
    category = Column(String, default="YUNO_TOOLS")  # YUNO_TOOLS | EXTERNAL_AGENT | PLATFORM_INTEGRATION
    created_at = Column(DateTime, default=datetime.utcnow)

    tools = relationship("MCPTool", back_populates="server", cascade="all, delete-orphan")


class MCPTool(Base):
    __tablename__ = "mcp_tools"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, default="")
    input_schema = Column(JSON, default={})  # JSON Schema definition of tool arguments
    enabled = Column(Boolean, default=True)
    exposure = Column(String, default="BUILDER_VISIBLE")  # BUILDER_VISIBLE | AGENT_ASSIGNABLE | PLATFORM_INTERNAL
    risk_level = Column(String, default="LOW")  # LOW | MEDIUM | HIGH | CRITICAL
    requires_approval = Column(Boolean, default=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("MCPServer", back_populates="tools")
    agent_assignments = relationship("AgentMCPTool", back_populates="mcp_tool", cascade="all, delete-orphan")


class AgentMCPTool(Base):
    __tablename__ = "agent_mcp_tools"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    mcp_tool_id = Column(Integer, ForeignKey("mcp_tools.id", ondelete="CASCADE"), nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    mcp_tool = relationship("MCPTool", back_populates="agent_assignments")
