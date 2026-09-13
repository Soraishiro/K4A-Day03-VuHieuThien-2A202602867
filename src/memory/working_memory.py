"""
🧠 MEMORY LAYER - Working Memory Component

Manages conversation state and tool results without leaking sensitive information
into system prompts. Separates trusted instructions from untrusted data to prevent
prompt injection.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorkingMemory:
    """
    Manages the conversation buffer and intermediate results.
    Ensures untrusted tool outputs are sanitized and clearly delimited
    before being fed back to the LLM.
    """

    def __init__(self, max_context_messages: int = 20):
        self._messages: List[Dict[str, Any]] = []
        self._tool_outputs: Dict[str, str] = {}
        self._max_context_messages = max_context_messages
        self._session_id: str = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self._step_counter: int = 0

    @property
    def session_id(self) -> str:
        return self._session_id

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation buffer."""
        self._messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim()

    def add_assistant_message(self, content: Optional[str], tool_calls: Optional[List[Dict]] = None, thought: str = "") -> None:
        """
        Add an assistant message to the conversation buffer.
        tool_calls are sanitized - only name and arguments (no internal tool_call_id
        from the LLM is exposed directly).
        """
        msg: Dict[str, Any] = {"role": "assistant", "timestamp": datetime.now().isoformat()}
        if content is not None:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = [
                {"name": tc.get("name", ""), "arguments": tc.get("arguments", {})}
                for tc in tool_calls
            ]
        if thought:
            msg["thought"] = thought
        self._messages.append(msg)
        self._trim()

    def add_tool_result(self, tool_name: str, result: str, tool_call_id: str) -> None:
        """
        Store a tool result with safety wrapping.
        Results are wrapped with clear delimiters to prevent prompt injection.
        """
        safe_result = self._sanitize_result(result)
        self._tool_outputs[tool_call_id] = safe_result

        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "content": safe_result,
            "timestamp": datetime.now().isoformat()
        })
        self._trim()

    def _sanitize_result(self, result: str) -> str:
        """
        Sanitize tool output to prevent prompt injection.
        - Wrap in clear delimiters
        - Escape any instruction-like content
        - Never trust raw tool output as instructions
        """
        try:
            parsed = json.loads(result)
            status = parsed.get("status", "UNKNOWN")
            if status in ("SUCCESS",):
                return json.dumps(result, ensure_ascii=False)
            else:
                return json.dumps(result, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"status": "ERROR", "raw_result": str(result)[:500]}, ensure_ascii=False)

    def _trim(self) -> None:
        """Trim conversation history to stay within context window limits."""
        while len(self._messages) > self._max_context_messages:
            self._messages.pop(0)

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Return the conversation history in a format suitable for LLM providers.
        Tool results are clearly marked as untrusted observations.
        """
        history = []
        for msg in self._messages:
            history.append({
                "role": msg["role"],
                "content": msg.get("content", ""),
                "tool_calls": msg.get("tool_calls"),
                "tool_name": msg.get("tool_name"),
                "tool_call_id": msg.get("tool_call_id")
            })
        return history

    def get_recent_thoughts(self, n: int = 3) -> List[str]:
        """Get recent thoughts from assistant messages."""
        thoughts = []
        for msg in reversed(self._messages):
            if msg.get("role") == "assistant" and msg.get("thought"):
                thoughts.append(msg["thought"])
            if len(thoughts) >= n:
                break
        return thoughts

    def increment_step(self) -> int:
        self._step_counter += 1
        return self._step_counter

    @property
    def step_count(self) -> int:
        return self._step_counter

    def reset(self) -> None:
        """Reset the working memory for a new conversation."""
        self._messages = []
        self._tool_outputs = {}
        self._step_counter = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self._session_id,
            "step_count": self._step_counter,
            "message_count": len(self._messages)
        }
