from typing import Any, Dict, List
from app.models.mcp_server import MCPTool


class MCPToolAdapter:
    """
    Adapts MCP Tool JSON-RPC definitions into standard OpenAI/LangChain tool function schemas.
    """

    @staticmethod
    def to_openai_function(mcp_tool: MCPTool, server_name: str) -> Dict[str, Any]:
        """
        Converts MCPTool DB record into OpenAI function representation:
        {
            "type": "function",
            "function": {
                "name": "mcp::server_name::tool_name",
                "description": "...",
                "parameters": { ... }
            }
        }
        """
        safe_server = server_name.replace("-", "_")
        qualified_name = f"mcp_{safe_server}_{mcp_tool.name}"
        input_schema = mcp_tool.input_schema or {}

        # Ensure parameters object conforms to JSON Schema draft expectations
        parameters = {
            "type": input_schema.get("type", "object"),
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", []),
        }

        return {
            "type": "function",
            "function": {
                "name": qualified_name,
                "description": mcp_tool.description or f"MCP Tool {mcp_tool.name} from {server_name}",
                "parameters": parameters,
            },
        }

    @staticmethod
    def to_openai_functions_batch(mcp_tools: List[MCPTool], server_name_map: Dict[int, str]) -> List[Dict[str, Any]]:
        """
        Adapts a list of MCPTool records into OpenAI function definitions.
        """
        adapted = []
        for tool in mcp_tools:
            server_name = server_name_map.get(tool.server_id, "unknown")
            adapted.append(MCPToolAdapter.to_openai_function(tool, server_name))
        return adapted
