import logging
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.mcp_server import AgentMCPTool, MCPTool, MCPServer
from app.mcp.client import MCPClientSession
from app.mcp.exceptions import MCPToolNotFoundError

logger = logging.getLogger(__name__)


class MCPToolRegistry:

    @staticmethod
    def discover_and_cache_tools(db: Session, server: MCPServer) -> List[MCPTool]:
        """
        Connects to the target MCP server, sends `tools/list` JSON-RPC request,
        validates tool definitions, and updates/caches them in PostgreSQL.
        """
        session = MCPClientSession(
            server_name=server.name,
            transport=server.transport,
            command=server.command,
            args=server.args,
            url=server.url,
            env=server.env_vars or {},
        )

        raw_tools = session.list_tools()
        logger.info(f"Discovered {len(raw_tools)} tools from MCP server '{server.name}'")

        cached_tools: List[MCPTool] = []
        existing_tools_map = {t.name: t for t in server.tools}

        for raw_tool in raw_tools:
            tool_name = raw_tool.get("name")
            if not tool_name:
                continue

            description = raw_tool.get("description", "")
            input_schema = raw_tool.get("inputSchema", {})

            if tool_name in existing_tools_map:
                # Update existing record
                tool_record = existing_tools_map[tool_name]
                tool_record.description = description
                tool_record.input_schema = input_schema
                tool_record.discovered_at = datetime.utcnow()
            else:
                # Insert new record
                tool_record = MCPTool(
                    server_id=server.id,
                    name=tool_name,
                    description=description,
                    input_schema=input_schema,
                    enabled=True,
                    discovered_at=datetime.utcnow(),
                )
                db.add(tool_record)

            cached_tools.append(tool_record)

        db.commit()
        for t in cached_tools:
            db.refresh(t)

        return cached_tools

    @staticmethod
    def get_agent_authorized_tools(db: Session, agent_id: int) -> List[Tuple[MCPTool, str]]:
        """
        Retrieves all enabled MCP tools authorized for the specified agent_id.
        Returns a list of tuples: (MCPTool, server_name).
        """
        assignments = (
            db.query(AgentMCPTool)
            .filter(AgentMCPTool.agent_id == agent_id, AgentMCPTool.enabled == True)
            .all()
        )

        results = []
        for assign in assignments:
            mcp_tool = assign.mcp_tool
            if mcp_tool and mcp_tool.enabled and mcp_tool.server and mcp_tool.server.enabled:
                results.append((mcp_tool, mcp_tool.server.name))

        return results
