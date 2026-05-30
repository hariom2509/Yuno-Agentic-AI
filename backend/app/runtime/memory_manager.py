"""
Redis-backed conversation memory for agents.

Stores per-agent conversation history keyed by (agent_name, execution_context).
Enables agents to maintain context across workflow steps when memory_enabled=True.
"""

import json
import logging
import os

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MEMORY_TTL = 3600 * 24  # 24 hours


class MemoryManager:
    """
    Manages short-term and cross-execution memory for agents.

    Memory is stored in Redis with TTL-based expiration.
    Keys follow the pattern: agent_memory:{agent_name}:{context_key}
    """

    def __init__(self):
        try:
            self._redis = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
            self._redis.ping()
            self._available = True
        except Exception as e:
            logger.warning(f"Redis unavailable for memory — falling back to in-memory: {e}")
            self._redis = None
            self._available = False
            self._local: dict[str, list[dict]] = {}

    def _key(self, agent_name: str, context: str = "default") -> str:
        safe_name = agent_name.lower().replace(" ", "_")
        return f"agent_memory:{safe_name}:{context}"

    def store(self, agent_name: str, role: str, content: str, context: str = "default"):
        """Append a message to the agent's conversation memory."""
        entry = {"role": role, "content": content[:2000]}
        key = self._key(agent_name, context)

        if self._available:
            try:
                existing = self._redis.get(key)
                history = json.loads(existing) if existing else []
                history.append(entry)
                # Keep last 20 messages to avoid context overflow
                history = history[-20:]
                self._redis.setex(key, MEMORY_TTL, json.dumps(history))
            except Exception as e:
                logger.warning(f"Memory store failed: {e}")
        else:
            self._local.setdefault(key, []).append(entry)
            self._local[key] = self._local[key][-20:]

    def recall(self, agent_name: str, context: str = "default") -> list[dict]:
        """Retrieve the agent's conversation history."""
        key = self._key(agent_name, context)

        if self._available:
            try:
                data = self._redis.get(key)
                return json.loads(data) if data else []
            except Exception as e:
                logger.warning(f"Memory recall failed: {e}")
                return []
        else:
            return self._local.get(key, [])

    def clear(self, agent_name: str, context: str = "default"):
        """Clear an agent's memory for a given context."""
        key = self._key(agent_name, context)

        if self._available:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        else:
            self._local.pop(key, None)

    def build_messages(
        self,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
        context: str = "default",
    ) -> list[dict]:
        """
        Build a full message array for an OpenAI-compatible chat call,
        including memory if available.
        """
        messages = [{"role": "system", "content": system_prompt}]

        history = self.recall(agent_name, context)
        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_prompt})
        return messages


# Singleton
memory = MemoryManager()