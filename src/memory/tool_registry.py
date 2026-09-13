"""
🧠 MEMORY LAYER - Tool Registry Component

Dynamically discovers tools from MCP servers without hardcoding tool descriptions
in system prompts. Prevents prompt injection by never exposing implementation details.
"""

import json
from typing import Dict, Any, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server import MCPAcademicServer


class ToolRegistry:
    """
    Dynamic tool registry that fetches tool schemas from MCP servers at runtime.
    Decouples the agent from specific tool implementations by only exposing
    tool name, description, and parameters (NOT implementation details).
    """

    def __init__(self, mcp_server: MCPAcademicServer):
        self._mcp_server = mcp_server
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tool_names: List[str] = []
        self._refresh()

    def _refresh(self) -> None:
        """Fetch tool schemas from MCP server and cache them."""
        tools = self._mcp_server.list_tools()
        self._tools_cache = tools
        self._tool_names = [t["name"] for t in tools] if tools else []

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Return only the public schema (name, description, parameters) for each tool.
        This is what gets passed to the LLM via the 'tools' parameter - never the
        implementation logic or internal data.
        """
        if self._tools_cache is None:
            self._refresh()
        return self._tools_cache or []

    def get_tool_names(self) -> List[str]:
        """Return list of available tool names."""
        if self._tools_cache is None:
            self._refresh()
        return self._tool_names

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool by name."""
        if self._tools_cache is None:
            self._refresh()
        for tool in self._tools_cache or []:
            if tool["name"] == tool_name:
                return tool
        return None

    def contains_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self.get_tool_names()

    def format_for_llm(self) -> str:
        """
        Format tool schemas as a human-readable string for inclusion in prompts.
        Only includes name, description, and parameter names (not full internal details).
        Used as fallback for LLMs that don't support structured tool calling.
        """
        if self._tools_cache is None:
            self._refresh()
        lines = []
        for i, tool in enumerate(self._tools_cache or [], 1):
            params = tool.get("parameters", {})
            param_names = list(params.get("properties", {}).keys()) if isinstance(params, dict) else []
            required = params.get("required", []) if isinstance(params, dict) else []
            req_str = f" (bắt buộc: {', '.join(required)})" if required else ""
            lines.append(f"{i}. {tool['name']}: {tool['description']}")
            lines.append(f"   Parameters: {', '.join(param_names)}{req_str}")
        return "\n".join(lines)
