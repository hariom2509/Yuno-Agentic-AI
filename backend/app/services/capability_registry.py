import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.mcp_server import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """
    Central Security Gateway and Capability Registry for Yuno AI.
    
    Categorizes all platform capabilities into 3 distinct tiers:
      - BUILDER_VISIBLE (Workflow Tools)
      - AGENT_ASSIGNABLE (Agent External Integrations)
      - PLATFORM_INTERNAL (Internal Runtime Policies & Automation)
    """

    @staticmethod
    def get_builder_tools(db: Session) -> Dict[str, Any]:
        """
        Returns only BUILDER_VISIBLE tools, formatted cleanly for the Visual Builder.
        Excludes all internal platform tools (GitHub, Postgres admin, internal hooks).
        """
        tools = (
            db.query(MCPTool)
            .join(MCPServer)
            .filter(
                MCPTool.enabled == True,
                MCPTool.exposure == "BUILDER_VISIBLE",
                MCPServer.enabled == True,
            )
            .all()
        )

        groups_map: Dict[str, List[Dict[str, Any]]] = {}
        for t in tools:
            server_name = t.server.name if t.server else "system"
            display_name = t.name.replace("_", " ").title()
            
            tool_item = {
                "id": f"mcp::{server_name}::{t.name}",
                "canonical_name": f"mcp::{server_name}::{t.name}",
                "short_name": t.name,
                "label": display_name,
                "description": t.description,
                "risk_level": t.risk_level,
                "requires_approval": t.requires_approval,
            }
            
            if server_name not in groups_map:
                groups_map[server_name] = []
            groups_map[server_name].append(tool_item)

        groups = []
        for s_name, t_list in groups_map.items():
            friendly_group_name = "Yuno Tools" if s_name == "yuno-tools" else s_name.replace("-", " ").title()
            groups.append({
                "id": s_name,
                "name": friendly_group_name,
                "tools": t_list,
            })

        return {"groups": groups}

    @staticmethod
    def get_agent_assignable_tools(db: Session) -> List[Dict[str, Any]]:
        """
        Returns tools eligible for assignment to autonomous Agents (e.g. Postgres MCP).
        """
        tools = (
            db.query(MCPTool)
            .join(MCPServer)
            .filter(
                MCPTool.enabled == True,
                MCPTool.exposure == "AGENT_ASSIGNABLE",
                MCPServer.enabled == True,
            )
            .all()
        )

        results = []
        for t in tools:
            results.append({
                "id": t.id,
                "canonical_name": f"mcp::{t.server.name}::{t.name}",
                "server_name": t.server.name,
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level,
                "requires_approval": t.requires_approval,
            })
        return results

    @staticmethod
    def get_execution_policy(db: Session, tool_identifier: str) -> Dict[str, Any]:
        """
        Resolves execution policy (requires_approval, risk_level, exposure)
        for any tool call by name or canonical identifier.
        """
        tool_identifier = tool_identifier or ""
        tool_name = tool_identifier
        server_name = None

        if tool_identifier.startswith("mcp::"):
            parts = tool_identifier.split("::")
            if len(parts) == 3:
                _, server_name, tool_name = parts

        query = db.query(MCPTool).filter(MCPTool.name == tool_name)
        if server_name:
            query = query.join(MCPServer).filter(MCPServer.name == server_name)

        tool_row = query.first()
        if tool_row:
            return {
                "requires_approval": tool_row.requires_approval,
                "risk_level": tool_row.risk_level,
                "exposure": tool_row.exposure,
                "enabled": tool_row.enabled and (tool_row.server.enabled if tool_row.server else True),
                "server_name": tool_row.server.name if tool_row.server else server_name,
            }

    @staticmethod
    def resolve_canonical_name(tool_identifier: str) -> str:
        """
        Maps legacy tool identifiers to canonical MCP names.
        Examples:
          'mcp::yuno-native-mcp::analyze_text' -> 'mcp::yuno-tools::analyze_text'
          'web_search' -> 'mcp::yuno-tools::web_search'
        """
        if not tool_identifier:
            return "mcp::yuno-tools::web_search"

        if tool_identifier.startswith("mcp::yuno-native-mcp::"):
            suffix = tool_identifier.split("::")[-1]
            return f"mcp::yuno-tools::{suffix}"

        if tool_identifier.startswith("mcp_postgres_mcp_"):
            suffix = tool_identifier.replace("mcp_postgres_mcp_", "")
            return f"mcp::postgres-mcp::{suffix}"
        if tool_identifier.startswith("mcp_yuno_tools_"):
            suffix = tool_identifier.replace("mcp_yuno_tools_", "")
            return f"mcp::yuno-tools::{suffix}"
        if tool_identifier.startswith("mcp_github_mcp_"):
            suffix = tool_identifier.replace("mcp_github_mcp_", "")
            return f"mcp::github-mcp::{suffix}"

        legacy_builtins = {
            "web_search": "mcp::yuno-tools::web_search",
            "calculator": "mcp::yuno-tools::calculator",
            "report_generator": "mcp::yuno-tools::report_generator",
            "file_reader": "mcp::yuno-tools::file_reader",
            "analyze_text": "mcp::yuno-tools::analyze_text",
            "calculate_metrics": "mcp::yuno-tools::calculate_metrics",
            "format_report": "mcp::yuno-tools::format_report",
        }
        if tool_identifier in legacy_builtins:
            return legacy_builtins[tool_identifier]

        return tool_identifier

    @staticmethod
    def get_tools_for_server(db: Session, server_name: str) -> List[Dict[str, Any]]:
        """
        Returns ONLY the enabled tools registered under a specific MCP server,
        adapted into OpenAI Function Calling schemas.
        Extremely token-efficient (~100 tokens vs thousands).
        """
        tools = (
            db.query(MCPTool)
            .join(MCPServer)
            .filter(
                MCPServer.name == server_name,
                MCPServer.enabled == True,
                MCPTool.enabled == True,
            )
            .all()
        )

        from app.mcp.adapter import MCPToolAdapter
        server_map = {t.server_id: server_name for t in tools}
        return MCPToolAdapter.to_openai_functions_batch(tools, server_map)

    @staticmethod
    def classify_and_scope_tools(db: Session, prompt: str) -> Dict[str, Any]:
        """
        Fast, deterministic category router.
        Evaluates prompt keywords to assign target MCP server scope:
          - Database related -> 'postgres-mcp'
          - Platform general -> 'yuno-tools'
        Returns: {"category": str, "server_name": str, "tools": List[Dict]}
        """
        prompt_lower = (prompt or "").lower()
        db_keywords = {
            "table", "tables", "postgres", "sql", "database", "schema",
            "select", "query", "insert", "rows", "truncate", "drop", "column"
        }

        # Match words in prompt
        words = set(prompt_lower.replace(",", " ").replace(".", " ").split())
        is_db_task = bool(words.intersection(db_keywords))

        target_server = "postgres-mcp" if is_db_task else "yuno-tools"
        category = "DATABASE" if is_db_task else "GENERAL"

        scoped_tools = CapabilityRegistry.get_tools_for_server(db, target_server)

        logger.info(
            f"[Category Router] Prompt classified as '{category}' -> Scoped to MCP server '{target_server}' "
            f"({len(scoped_tools)} tools loaded)"
        )

        return {
            "category": category,
            "server_name": target_server,
            "tools": scoped_tools,
        }
