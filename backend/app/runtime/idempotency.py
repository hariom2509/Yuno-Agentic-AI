"""
Idempotency Guard for Side-Effecting MCP Tool Calls

Problem:  A LangGraph graph resumed after a crash or HITL approval will re-execute
          all nodes from the checkpoint. Without protection, a `create_issue` tool
          call would fire again — creating duplicate GitHub issues, duplicate DB writes, etc.

Solution: Before executing any MCP tool call, compute a deterministic SHA-256 key:
              key = SHA-256("{execution_id}:{node_id}:{tool_name}")[:16]
          If the key has been seen before, skip execution and return a shield message.
          If not, mark it executed and proceed.

Key Properties:
  - Deterministic: same inputs → same key → guaranteed idempotency
  - Scoped: different executions produce different keys (execution_id isolates)
  - Replay-safe: crash-and-resume does not double-fire side effects

Storage:
  Development: in-process set (cleared on restart — suitable with MemorySaver)
  Production:  Redis SADD + EXPIRE for cross-process + cross-restart durability
               (implement IdempotencyGuard.is_executed / mark_executed with Redis)

Example key computation:
  execution_id=42, node_id="node_github", tool_name="mcp::github-mcp::create_issue"
  raw = "42:node_github:mcp::github-mcp::create_issue"
  key = sha256(raw)[:16]  →  "3a7b9c1d4e2f0a8b"
"""
import hashlib
import logging
from typing import Set

logger = logging.getLogger(__name__)

# Module-level executed key registry.
# Production: replace with Redis SADD/SISMEMBER calls with per-execution TTL.
_executed_keys: Set[str] = set()


class IdempotencyGuard:
    """
    SHA-256-keyed idempotency shield for side-effecting MCP tool executions.
    Prevents duplicate API calls, DB mutations, and external state changes
    when a LangGraph graph is replayed from a checkpoint.
    """

    @staticmethod
    def compute_key(execution_id: int, node_id: str, tool_name: str) -> str:
        """
        Computes a 16-char hex SHA-256 idempotency key.

        Args:
            execution_id: Yuno Execution.id — scopes key to one workflow run
            node_id:      ReactFlow node ID — scopes key to one graph node
            tool_name:    Full tool name e.g. "mcp::github-mcp::create_issue"

        Returns:
            16-character deterministic hex string
        """
        raw = f"{execution_id}:{node_id}:{tool_name}"
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return key

    @staticmethod
    def is_executed(key: str) -> bool:
        """Returns True if this exact tool invocation has already been executed."""
        return key in _executed_keys

    @staticmethod
    def mark_executed(key: str) -> None:
        """
        Registers a key as executed.
        Must be called immediately before the side-effecting tool call
        (not after) to prevent double execution on process kill during the call.
        """
        _executed_keys.add(key)
        logger.debug(f"[Idempotency] Key registered: {key}")

    @staticmethod
    def clear_all() -> None:
        """Clears the entire registry. Used in testing."""
        _executed_keys.clear()
        logger.info("[Idempotency] Registry cleared.")
