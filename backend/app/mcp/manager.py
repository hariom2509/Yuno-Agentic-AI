import logging
import os
import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.mcp_server import MCPServer
from app.mcp.client import MCPClientSession
from app.mcp.authorization import MCPAuthorizationService
from app.mcp.exceptions import MCPConnectionError, MCPSecurityError, MCPToolNotFoundError

logger = logging.getLogger(__name__)

# Approved executable commands for stdio transport security
APPROVED_STDIO_COMMANDS = {"npx", "python", "python3", "node", "uvx", "docker"}


class MCPManager:
    """
    Singleton Manager for MCP session lifecycle, connection pooling, security allowlisting,
    secret resolution, and tool execution dispatching.
    """

    _instance = None
    _sessions: Dict[str, MCPClientSession] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls)
            cls._sessions = {}
        return cls._instance

    @classmethod
    def get_session(cls, db: Session, server_name: str) -> MCPClientSession:
        """
        Gets an existing active session from the pool or creates and validates a new session.
        """
        server = db.query(MCPServer).filter(MCPServer.name == server_name, MCPServer.enabled == True).first()
        if not server:
            raise MCPToolNotFoundError(f"MCP server '{server_name}' not found or disabled.")

        # Security check: validate command allowlist for stdio transport
        if server.transport == "stdio":
            cmd_basename = os.path.basename(server.command or "").lower()
            if cmd_basename not in APPROVED_STDIO_COMMANDS:
                raise MCPSecurityError(
                    f"Command '{server.command}' is not in approved stdio command allowlist: {APPROVED_STDIO_COMMANDS}"
                )

        # Check session pool
        if server_name in cls._sessions:
            return cls._sessions[server_name]

        # Resolve secret references
        env_vars = dict(server.env_vars or {})
        if server.secret_reference:
            resolved_secret = cls._resolve_secret(server.secret_reference)
            if resolved_secret and not resolved_secret.startswith("env:"):
                env_vars["MCP_AUTH_TOKEN"] = resolved_secret
                env_vars["GITHUB_PERSONAL_ACCESS_TOKEN"] = resolved_secret
        
        # Fallback env lookup for github token if not in secret_reference
        if "GITHUB_PERSONAL_ACCESS_TOKEN" not in env_vars:
            pat = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
            if pat:
                env_vars["GITHUB_PERSONAL_ACCESS_TOKEN"] = pat

        session = MCPClientSession(
            server_name=server.name,
            transport=server.transport,
            command=server.command,
            args=server.args,
            url=server.url,
            env=env_vars,
        )

        cls._sessions[server_name] = session
        return session

    @classmethod
    def call_tool(
        cls,
        db: Session,
        agent_id: Optional[int],
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main execution entry point:
        1. If agent_id is provided, verifies tool-level authorization.
        2. Retrieves pooled/validated session.
        3. Executes tool call and tracks execution metrics (latency & status).
        """
        start_time = time.time()

        if agent_id is not None:
            MCPAuthorizationService.verify_agent_tool_access(db, agent_id, server_name, tool_name)

        session = cls.get_session(db, server_name)
        result = session.call_tool(tool_name, arguments)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(f"MCP Tool Execution: '{server_name}::{tool_name}' completed in {latency_ms}ms")

        return {
            "status": "success",
            "server": server_name,
            "tool": tool_name,
            "result": result,
            "latency_ms": latency_ms,
        }

    @classmethod
    def clear_sessions(cls):
        """Clears the session pool."""
        cls._sessions.clear()

    @staticmethod
    def _resolve_secret(secret_ref: str) -> Optional[str]:
        """
        Resolves a secret reference string.
        Examples:
        - "env:GITHUB_TOKEN" -> reads OS env var GITHUB_TOKEN
        - "token_string" -> literal key string fallback
        """
        if secret_ref.startswith("env:"):
            env_key = secret_ref.split("env:", 1)[1]
            return os.getenv(env_key)
        return secret_ref
