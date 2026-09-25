from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPServerCreate(BaseModel):
    name: str = Field(..., description="Unique name of the MCP server, e.g., 'github-server'")
    description: str = Field("", description="Human-readable description of the server capabilities")
    transport: str = Field("stdio", description="Transport layer: 'stdio' or 'http'")
    command: Optional[str] = Field(None, description="Command to execute for stdio transport (e.g. 'npx', 'python')")
    args: Optional[List[str]] = Field(default=[], description="Arguments for stdio command")
    url: Optional[str] = Field(None, description="URL endpoint for HTTP streamable transport")
    secret_reference: Optional[str] = Field(None, description="Reference key for secret management lookup")
    env_vars: Optional[Dict[str, str]] = Field(default={}, description="Environment variables dictionary")
    enabled: bool = True


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    secret_reference: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None


class MCPToolResponse(BaseModel):
    id: int
    server_id: int
    name: str
    description: str
    input_schema: Dict[str, Any] = {}
    enabled: bool = True
    exposure: str = "BUILDER_VISIBLE"
    risk_level: str = "LOW"
    requires_approval: bool = False
    discovered_at: datetime

    class Config:
        from_attributes = True


class MCPToolUpdate(BaseModel):
    exposure: Optional[str] = None  # BUILDER_VISIBLE | AGENT_ASSIGNABLE | PLATFORM_INTERNAL
    risk_level: Optional[str] = None  # LOW | MEDIUM | HIGH | CRITICAL
    requires_approval: Optional[bool] = None
    enabled: Optional[bool] = None


class MCPServerResponse(BaseModel):
    id: int
    name: str
    description: str
    transport: str
    command: Optional[str] = None
    args: List[str] = []
    url: Optional[str] = None
    secret_reference: Optional[str] = None
    env_vars: Dict[str, str] = {}
    enabled: bool
    created_at: datetime
    tools: List[MCPToolResponse] = []

    class Config:
        from_attributes = True


class AgentMCPToolAssign(BaseModel):
    mcp_tool_ids: List[int] = Field(..., description="List of MCPTool IDs authorized for the agent")


class MCPDiscoverResponse(BaseModel):
    server_id: int
    server_name: str
    tools_count: int
    tools: List[MCPToolResponse]
