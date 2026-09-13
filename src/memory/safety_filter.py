"""
🧠 MEMORY LAYER - Safety Filter Component

Provides prompt injection prevention by sanitizing untrusted data before
it is incorporated into LLM prompts. Implements defense-in-depth by:
1. Detecting injection patterns in tool outputs
2. Wrapping untrusted data in clear delimiters
3. Escaping instruction-like sequences
"""

import json
import re
from typing import Dict, Any, Optional, Tuple


class SafetyFilter:
    """
    Filters untrusted tool outputs to prevent prompt injection attacks.
    """

    INJECTION_PATTERNS = [
        re.compile(r'^(system|instruction|prompt)\s*[:\s]', re.IGNORECASE),
        re.compile(r'(?i)(you are|you must|you should|always|never|must|required)', re.IGNORECASE),
        re.compile(r'(?i)(system prompt|override|ignore|disregard|bypass|jailbreak)', re.IGNORECASE),
    ]

    MAX_OUTPUT_LENGTH = 2000

    @classmethod
    def sanitize(cls, content: str) -> str:
        """
        Sanitize untrusted content from tool outputs.
        Returns JSON-wrapped content to prevent injection.
        """
        if not isinstance(content, str):
            content = str(content)

        truncated = content[:cls.MAX_OUTPUT_LENGTH]

        injection_detected = cls._detect_injection(truncated)

        safe_content = json.dumps({
            "injection_detected": injection_detected,
            "data": truncated
        }, ensure_ascii=False)

        return safe_content

    @classmethod
    def _detect_injection(cls, content: str) -> bool:
        """Detect potential prompt injection patterns."""
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(content):
                return True
        return False

    @classmethod
    def wrap_observation(cls, tool_name: str, result: str) -> str:
        """
        Wrap a tool result as an observation with clear delimiters.
        This makes it visually distinct from instructions.
        """
        sanitized = cls.sanitize(result)
        wrapped = f"<tool_observation tool_name=\"{tool_name}\">\n{sanitized}\n</tool_observation>"
        return wrapped

    @classmethod
    def filter_system_prompt(cls, prompt: str) -> str:
        """
        Validate that the system prompt doesn't contain user-controlled content.
        Should be called at application startup.
        """
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(prompt):
                return prompt

        return prompt

    @classmethod
    def should_reject_tool_args(cls, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check tool arguments for suspicious content that might be an injection
        attempt through tool parameters.
        """
        for key, value in arguments.items():
            if isinstance(value, str):
                for pattern in cls.INJECTION_PATTERNS:
                    if pattern.search(value):
                        return True, f"Potential injection in parameter '{key}'"
        return False, None
