"""
🛡️ GUARDRAIL AGENT - Safety Layer

Implements a two-agent system where a separate Guardrail Agent monitors
the Execution Agent's actions without being able to execute tools itself.
This decouples safety decisions from execution, making the system more
resilient to prompt injection.

Reference: https://www.anthropic.com/research/developing-ram-safe-hai
"""

import json
from typing import Dict, Any, List, Optional, Tuple


class GuardrailAgent:
    """
    A safety-monitoring agent that reviews tool calls before execution.
    
    The GuardrailAgent can see:
    - User's original query
    - Tool schemas available
    - Proposed tool call (name + arguments)
    
    The GuardrailAgent CANNOT:
    - Execute any tools
    - Modify data
    - Access external systems
    
    It only returns APPROVE or REJECT with reasoning.
    """

    ALLOWED_TOOLS = frozenset({
        "academic_query",
        "course_catalog_query",
        "schedule_appointment",
        "curriculum_query"
    })

    ALLOWED_TOOL_CONTEXTS = {
        "academic_query": {
            "requires_self_lookup": False,
        },
        "schedule_appointment": {
            "requires_self_lookup": True,
        },
        "course_catalog_query": {
            "requires_self_lookup": False,
        },
        "curriculum_query": {
            "requires_self_lookup": False,
        }
    }

    INJECTION_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous",
        "system prompt",
        "override safety",
        "bypass guardrail",
    ]

    def __init__(self):
        self._blocked_patterns = self.INJECTION_PATTERNS
        self._self_student_ids = {"SV2026001"}
        self._access_log: List[Dict[str, Any]] = []

    def review_tool_call(self, tool_name: str, arguments: Dict[str, Any], 
                         user_query: str, chat_history: List[Dict]) -> Tuple[bool, str]:
        """
        Review a proposed tool call and decide whether to approve or reject it.
        
        Returns:
            (approved, reason) tuple
            - If approved: (True, "")
            - If rejected: (False, reason_string)
        """
        self._access_log.append({
            "tool": tool_name,
            "args": arguments,
            "user_query": user_query,
            "history_len": len(chat_history)
        })

        if tool_name not in self.ALLOWED_TOOLS:
            return False, f"Lỗi bảo mật: Tool '{tool_name}' không nằm trong danh sách cho phép."

        for pattern in self._blocked_patterns:
            if pattern.lower() in json.dumps(arguments).lower():
                return False, f"Lỗi bảo mật: Nghi ngờ nội dung injection trong tham số tool."

        if tool_name in ("academic_query", "schedule_appointment") and "student_id" in arguments:
            sid = arguments.get("student_id", "")
            if sid not in self._self_student_ids:
                return False, f"Bảo mật: Sinh viên chỉ có thể truy vấn thông tin của chính mình ({', '.join(self._self_student_ids)})."

        context = self.ALLOWED_TOOL_CONTEXTS.get(tool_name, {})
        if context.get("requires_self_lookup", False) and "student_id" not in arguments:
            return False, f"Thiếu tham số bắt buộc: {tool_name} yêu cầu student_id."

        if not arguments:
            return False, f"Tham số tool trống: {tool_name} yêu cầu ít nhất một tham số."

        return True, ""

    def review_user_query(self, user_query: str) -> Tuple[bool, str]:
        """
        Review a raw user query for injection attempts.
        
        Returns:
            (safe, reason) tuple
        """
        query_lower = user_query.lower()
        for pattern in self._blocked_patterns:
            if pattern.lower() in query_lower:
                return False, f"Lỗi bảo mật: Nghi ngờ injection trong câu hỏi người dùng."

        dangerous_keywords = [
            "xóa", "delete", "sửa", "modify", "update", "thay đổi",
            "đổi mật khẩu", "reset", "hack", "bypass", "root",
            "quyền admin", "administrator", "code", "source",
            "mã nguồn", "database", "sql", "truy cập trực tiếp"
        ]

        for kw in dangerous_keywords:
            if kw.lower() in query_lower:
                return False, f"Lỗi bảo mật: Câu hỏi chứa từ khóa nguy hiểm '{kw}'."

        return True, ""

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Return the access log of all reviewed tool calls."""
        return self._access_log.copy()

    def reset_session(self) -> None:
        """Reset the guardrail state for a new session."""
        self._access_log = []

    def add_self_student_id(self, student_id: str) -> None:
        """Add a student ID that is allowed for self-lookup."""
        self._self_student_ids.add(student_id.strip().upper())

    def get_allowed_student_ids(self) -> List[str]:
        """Return the list of allowed student IDs for self-lookup."""
        return list(self._self_student_ids)
