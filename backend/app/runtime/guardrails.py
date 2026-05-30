"""
Guardrails engine for agent input/output safety.

Enforces configurable rules per agent:
- Blocked topics/keywords
- Output length limits
- Required output format validation
- Token budget enforcement
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class GuardrailResult:
    """Result of a guardrail check."""

    def __init__(self, passed: bool, reason: str = "", filtered_content: str = ""):
        self.passed = passed
        self.reason = reason
        self.filtered_content = filtered_content


class Guardrails:
    """
    Validates agent inputs and outputs against configurable rules.

    Config schema (stored as JSON on the Agent model):
    {
        "blocked_topics": ["violence", "illegal"],
        "max_output_length": 3000,
        "require_json": false,
        "allowed_domains": [],          # restrict web search to these domains
        "content_filter": true           # basic profanity/harmful content filter
    }
    """

    # Basic content filter patterns
    HARMFUL_PATTERNS = [
        r"\b(hack|exploit|attack)\s+(system|server|network)\b",
        r"\b(steal|phish)\s+(password|credential|data)\b",
    ]

    @staticmethod
    def check_input(content: str, config: dict) -> GuardrailResult:
        """Validate input before sending to agent."""
        if not config:
            return GuardrailResult(passed=True, filtered_content=content)

        # Check blocked topics
        blocked = config.get("blocked_topics", [])
        if blocked:
            content_lower = content.lower()
            for topic in blocked:
                if topic.lower() in content_lower:
                    return GuardrailResult(
                        passed=False,
                        reason=f"Input contains blocked topic: '{topic}'",
                    )

        # Basic content filter
        if config.get("content_filter", False):
            for pattern in Guardrails.HARMFUL_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    return GuardrailResult(
                        passed=False,
                        reason="Input flagged by content filter",
                    )

        return GuardrailResult(passed=True, filtered_content=content)

    @staticmethod
    def check_output(content: str, config: dict) -> GuardrailResult:
        """Validate output after agent generates it."""
        if not config:
            return GuardrailResult(passed=True, filtered_content=content)

        # Enforce max output length
        max_len = config.get("max_output_length", 0)
        if max_len and len(content) > max_len:
            content = content[:max_len] + "\n\n[Output truncated by guardrail]"

        # Validate JSON format if required
        if config.get("require_json", False):
            import json as json_mod
            try:
                json_mod.loads(content)
            except (json_mod.JSONDecodeError, TypeError):
                return GuardrailResult(
                    passed=False,
                    reason="Output does not match required JSON format",
                )

        # Check blocked topics in output
        blocked = config.get("blocked_topics", [])
        if blocked:
            content_lower = content.lower()
            for topic in blocked:
                if topic.lower() in content_lower:
                    return GuardrailResult(
                        passed=False,
                        reason=f"Output contains blocked topic: '{topic}'",
                    )

        return GuardrailResult(passed=True, filtered_content=content)

    @staticmethod
    def check_token_budget(tokens_used: int, max_tokens: int) -> GuardrailResult:
        """Check if execution is within token budget."""
        if max_tokens and tokens_used > max_tokens:
            return GuardrailResult(
                passed=False,
                reason=f"Token budget exceeded: {tokens_used}/{max_tokens}",
            )
        return GuardrailResult(passed=True)
