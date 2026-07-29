import logging
from sqlalchemy.orm import Session

from app.models.mcp_server import AgentMCPTool, MCPTool, MCPServer
from app.mcp.exceptions import MCPAuthorizationError, MCPToolNotFoundError

logger = logging.getLogger(__name__)


class MCPAuthorizationService:

    @staticmethod
    def verify_agent_tool_access(db: Session, agent_id: int, server_name: str, tool_name: str) -> MCPTool:
        """
        Verifies that:
        1. MCPServer exists and is enabled.
        2. MCPTool exists on that server and is enabled.
        3. Agent has an active AgentMCPTool record authorizing execution of this tool.
        """
        server = db.query(MCPServer).filter(MCPServer.name == server_name, MCPServer.enabled == True).first()
        if not server:
            raise MCPToolNotFoundError(f"MCP server '{server_name}' not found or is disabled.")

        mcp_tool = db.query(MCPTool).filter(
            MCPTool.server_id == server.id,
            MCPTool.name == tool_name,
            MCPTool.enabled == True
        ).first()

        if not mcp_tool:
            raise MCPToolNotFoundError(f"Tool '{tool_name}' not found on MCP server '{server_name}' or is disabled.")

        assignment = db.query(AgentMCPTool).filter(
            AgentMCPTool.agent_id == agent_id,
            AgentMCPTool.mcp_tool_id == mcp_tool.id,
            AgentMCPTool.enabled == True
        ).first()

        if not assignment:
            logger.warning(f"Unauthorized MCP tool execution attempt: Agent #{agent_id} -> '{server_name}::{tool_name}'")
            raise MCPAuthorizationError(
                f"Agent #{agent_id} is not authorized to execute tool '{tool_name}' from server '{server_name}'."
            )

        return mcp_tool
