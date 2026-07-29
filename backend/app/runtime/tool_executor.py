import logging
from app.tools.web_search_tool import search_web
from app.tools.calculator_tool import calculate
from app.tools.report_generator_tool import generate_report
from app.tools.file_reader_tool import read_file

logger = logging.getLogger(__name__)


class ToolExecutor:

    @staticmethod
    def execute(
        tool_name: str,
        payload: any,
        db=None,
        agent_id: int = None,
    ):
        """
        Executes a requested tool.
        Supports:
        1. Dynamic MCP Tools (format: `mcp::<server_name>::<tool_name>`)
        2. Custom Python Skill models
        """
        from app.services.capability_registry import CapabilityRegistry
        canonical_name = CapabilityRegistry.resolve_canonical_name(tool_name) or tool_name or ""

        # 1. Dynamic MCP Tool Execution
        if canonical_name.startswith("mcp::") and db is not None:
            parts = canonical_name.split("::")
            if len(parts) == 3:
                _, server_name, real_tool_name = parts
                try:
                    from app.mcp.manager import MCPManager
                    arguments = payload if isinstance(payload, dict) else {"query": str(payload), "text": str(payload), "expression": str(payload), "numbers": str(payload), "content": str(payload), "data": str(payload), "path": str(payload)}
                    
                    effective_agent_id = agent_id
                    if effective_agent_id is None and isinstance(payload, dict):
                        effective_agent_id = payload.get("agent_id")

                    res = MCPManager.call_tool(
                        db=db,
                        agent_id=effective_agent_id,
                        server_name=server_name,
                        tool_name=real_tool_name,
                        arguments=arguments,
                    )
                    return str(res.get("result", ""))
                except Exception as e:
                    logger.error(f"MCP execution failure for '{canonical_name}': {str(e)}")
                    return f"MCP Tool Execution Error: {str(e)}"

        # 3. Check Custom Skill DB Records
        if db:
            from app.models.skill import Skill
            skill = db.query(Skill).filter(Skill.name == tool_name, Skill.active == True).first()
            if skill:
                try:
                    local_env = {"payload": payload, "result": None}
                    exec(skill.code, {}, local_env)
                    return str(local_env.get("result", "Skill executed with no return result."))
                except Exception as e:
                    logger.error(f"Custom skill '{tool_name}' execution crashed: {e}")
                    raise ValueError(f"Custom skill execution failed: {str(e)}")

        return f"Tool '{tool_name}' not found."