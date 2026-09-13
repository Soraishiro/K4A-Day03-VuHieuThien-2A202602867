"""
Unit tests for mcp_server.py - MCP Server Implementation
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from mcp_server import MCPAcademicServer
from tools import TOOLS_SCHEMA


class TestMCPAcademicServer:
    """Test MCP Academic Server functionality"""

    def setup_method(self):
        self.server = MCPAcademicServer()

    def test_server_initialization(self):
        assert self.server.server_name == "vinuni-academic-mcp-server"
        assert self.server.version == "2026.1.0"

    def test_list_tools_returns_all_schemas(self):
        tools = self.server.list_tools()
        assert isinstance(tools, list)
        assert len(tools) == 4
        tool_names = {t["name"] for t in tools}
        assert tool_names == {"academic_query", "course_catalog_query", "schedule_appointment", "curriculum_query"}

    def test_list_tools_matches_tools_schema(self):
        tools = self.server.list_tools()
        assert len(tools) == len(TOOLS_SCHEMA)
        for t1, t2 in zip(tools, TOOLS_SCHEMA):
            assert t1["name"] == t2["name"]

    def test_call_tool_academic_query(self):
        result = self.server.call_tool("academic_query", {"student_id": "SV2026001"})
        assert result["jsonrpc"] == "2.0"
        assert result["server"] == "vinuni-academic-mcp-server"
        assert result["tool"] == "academic_query"
        assert "result" in result
        result_data = result["result"]
        assert result_data["status"] == "SUCCESS"
        assert result_data["student_id"] == "SV2026001"

    def test_call_tool_course_catalog_query(self):
        result = self.server.call_tool("course_catalog_query", {"course_name": "Trí tuệ nhân tạo"})
        assert result["jsonrpc"] == "2.0"
        assert result["server"] == "vinuni-academic-mcp-server"
        assert result["tool"] == "course_catalog_query"
        assert "result" in result
        result_data = result["result"]
        assert result_data["status"] == "SUCCESS"
        assert result_data["course_code"] == "AIC201"

    def test_call_tool_curriculum_query(self):
        result = self.server.call_tool("curriculum_query", {"program_code": "AI"})
        assert result["jsonrpc"] == "2.0"
        assert result["server"] == "vinuni-academic-mcp-server"
        assert result["tool"] == "curriculum_query"
        assert result["result"]["status"] == "SUCCESS"
        assert result["result"]["data"]["total_credits"] == 128
        assert result["result"]["data"]["min_gpa"] == 2.0

    def test_call_tool_schedule_appointment(self):
        result = self.server.call_tool("schedule_appointment", {
            "student_id": "SV2026001",
            "datetime_str": "14:00 15/09/2026",
            "advisor_name": "PGS.TS Nguyễn Văn A"
        })
        assert result["jsonrpc"] == "2.0"
        assert result["server"] == "vinuni-academic-mcp-server"
        assert result["tool"] == "schedule_appointment"
        assert "result" in result
        result_data = result["result"]
        assert result_data["status"] == "SUCCESS"
        assert "booking_id" in result_data

    def test_call_tool_unknown_tool(self):
        result = self.server.call_tool("unknown_tool", {})
        assert result["jsonrpc"] == "2.0"
        assert result["server"] == "vinuni-academic-mcp-server"
        assert result["tool"] == "unknown_tool"
        assert "result" in result
        result_data = result["result"]
        assert result_data["status"] == "UNKNOWN_TOOL"

    def test_call_tool_invalid_arguments(self):
        result = self.server.call_tool("academic_query", {"invalid_param": "value"})
        assert result["jsonrpc"] == "2.0"
        result_data = result["result"]
        assert result_data["status"] == "EXECUTION_ERROR"

    def test_jsonrpc_format(self):
        result = self.server.call_tool("academic_query", {"student_id": "SV2026001"})
        # Verify JSON-RPC 2.0 compliance
        assert result["jsonrpc"] == "2.0"
        assert "server" in result
        assert "tool" in result
        assert "result" in result
        # No "id" field in notification-style response (which is correct for this implementation)

    def test_custom_server_name(self):
        custom_server = MCPAcademicServer("custom-mcp-server")
        assert custom_server.server_name == "custom-mcp-server"
        result = custom_server.call_tool("academic_query", {"student_id": "SV2026001"})
        assert result["server"] == "custom-mcp-server"


class TestMCPServerIntegration:
    """Integration tests for MCP Server with actual tool execution"""

    def setup_method(self):
        self.server = MCPAcademicServer()

    def test_full_academic_query_flow(self):
        result = self.server.call_tool("academic_query", {"student_id": "SV2026001"})
        assert result["result"]["status"] == "SUCCESS"
        student_data = result["result"]["data"]
        assert student_data["full_name"] == "Nguyễn Văn An"
        assert student_data["gpa"] == 3.85
        assert student_data["credits_earned"] == 118
        assert "completed_courses" in student_data

    def test_full_schedule_appointment_flow(self):
        result = self.server.call_tool("schedule_appointment", {
            "student_id": "SV2026001",
            "datetime_str": "14:00 15/09/2026",
            "advisor_name": "PGS.TS Nguyễn Văn A",
            "reason": "Tư vấn đăng ký môn"
        })
        assert result["result"]["status"] == "SUCCESS"
        assert result["result"]["student_name"] == "Nguyễn Văn An"
        assert result["result"]["advisor"] == "PGS.TS Nguyễn Văn A"
        assert result["result"]["datetime"] == "14:00 15/09/2026"
        assert result["result"]["reason"] == "Tư vấn đăng ký môn"

    def test_multi_tool_sequence(self):
        # First query student
        result1 = self.server.call_tool("academic_query", {"student_id": "SV2026001"})
        assert result1["result"]["status"] == "SUCCESS"
        student_data = result1["result"]["data"]

        # Then query course
        result2 = self.server.call_tool("course_catalog_query", {"course_name": "Trí tuệ nhân tạo"})
        assert result2["result"]["status"] == "SUCCESS"
        course_data = result2["result"]["data"]

        # Then book appointment
        result3 = self.server.call_tool("schedule_appointment", {
            "student_id": "SV2026001",
            "datetime_str": "14:00 15/09/2026",
            "advisor_name": student_data["advisor"]
        })
        assert result3["result"]["status"] == "SUCCESS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])