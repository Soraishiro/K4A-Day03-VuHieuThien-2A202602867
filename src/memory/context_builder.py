"""
🧠 MEMORY LAYER - Context Builder Component

Builds the final prompt context for the LLM by combining:
1. A lean system prompt (trusted instructions only)
2. Tool schemas (from ToolRegistry, not hardcoded)
3. Conversation history (from WorkingMemory, safety-filtered)

Avoids polluting the system prompt with data or tool descriptions.
"""

import json
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.tool_registry import ToolRegistry
from memory.working_memory import WorkingMemory
from memory.safety_filter import SafetyFilter


class ContextBuilder:
    """
    Builds LLM prompts by combining system instructions, tool schemas,
    and conversation history without leaking sensitive information.
    """

    LEAN_SYSTEM_PROMPT = """Bạn là Trợ lý Tác tử Học vụ của Đại học VinUni.

QUY TẮC:
- Dùng công cụ để tra cứy thông tin thời gian thực (hồ sơ, lịch, môn học)
- Trả lời trực tiếp nếu là kiến thức chung (quy chế, cấu trúc chương trình)
- Gọi đúng công cụ với tham số chính xác; tổng hợp kết quả thành câu trả lời rõ ràng
- Không bịa đặt; nếu NOT_FOUND thì báo lịch sự
- Nếu user sai thông tin, đính chính dựa trên dữ liệu thực từ công cụ
- Tránh gọi tool nếu trả lời có thể cho từ kiến thức chung
- Tốt nghiệp: 128 tín chỉ + GPA ≥ 2.0
- Đăng ký môn: kiểm tra môn tiên quyết đã vượt chưa"""

    def __init__(self, tool_registry: ToolRegistry, working_memory: WorkingMemory):
        self._tool_registry = tool_registry
        self._working_memory = working_memory
        self._safety_filter = SafetyFilter()

    def build_system_prompt(self) -> str:
        """
        Return a lean system prompt with only high-level instructions.
        Tool descriptions are NOT included here - they are fetched dynamically
        via the tool registry and passed as structured 'tools' parameter.
        """
        return self._safety_filter.filter_system_prompt(self.LEAN_SYSTEM_PROMPT)

    def build_tool_specs(self) -> List[Dict[str, Any]]:
        """
        Build tool specifications for the LLM API call.
        Only schema (name, description, parameters) is exposed - no implementation.
        """
        return self._tool_registry.get_tool_descriptions()

    def build_chat_history(self) -> List[Dict[str, Any]]:
        """
        Return conversation history from working memory.
        All tool outputs are already safety-filtered.
        """
        return self._working_memory.get_chat_history()

    def build_context(self, user_query: str) -> Dict[str, Any]:
        """
        Build the complete context for an LLM call.
        Returns a dict with system_prompt, tools, and chat_history.
        """
        return {
            "system_prompt": self.build_system_prompt(),
            "tools": self.build_tool_specs(),
            "chat_history": self.build_chat_history(),
            "user_query": user_query
        }

    def get_tool_descriptions_string(self) -> Optional[str]:
        """
        Fallback: get tool descriptions as a string for LLMs that
        don't support structured tool calling.
        """
        tool_names = self._tool_registry.get_tool_names()
        if not tool_names:
            return None
        return self._tool_registry.format_for_llm()
