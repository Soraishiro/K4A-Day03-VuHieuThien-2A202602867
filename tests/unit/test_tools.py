"""
Unit tests for tools.py - Tool Schemas and Execution Layer
"""
import json
import pytest
from src.tools import (
    TOOLS_SCHEMA,
    execute_academic_query,
    execute_curriculum_query,
    execute_course_catalog_query,
    execute_schedule_appointment,
    dispatch_tool_call,
    MOCK_STUDENTS,
    MOCK_ADVISOR_SCHEDULE,
    MOCK_COURSE_CATALOG,
    MOCK_APPOINTMENTS,
)


class TestToolSchemas:
    """Test JSON Schema definitions for all tools"""

    def test_tools_schema_is_list(self):
        assert isinstance(TOOLS_SCHEMA, list)
        assert len(TOOLS_SCHEMA) == 4

    def test_academic_query_schema(self):
        tool = next(t for t in TOOLS_SCHEMA if t["name"] == "academic_query")
        assert tool["name"] == "academic_query"
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"
        assert "student_id" in tool["parameters"]["properties"]
        assert tool["parameters"]["required"] == ["student_id"]
        assert tool["parameters"]["properties"]["student_id"]["type"] == "string"

    def test_course_catalog_query_schema(self):
        tool = next(t for t in TOOLS_SCHEMA if t["name"] == "course_catalog_query")
        assert tool["name"] == "course_catalog_query"
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"
        assert "course_name" in tool["parameters"]["properties"]
        assert tool["parameters"]["required"] == ["course_name"]
        assert tool["parameters"]["properties"]["course_name"]["type"] == "string"

    def test_curriculum_query_schema(self):
        tool = next(t for t in TOOLS_SCHEMA if t["name"] == "curriculum_query")
        assert tool["name"] == "curriculum_query"
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"
        assert "program_code" in tool["parameters"]["properties"]
        assert tool["parameters"]["required"] == ["program_code"]
        assert tool["parameters"]["properties"]["program_code"]["type"] == "string"

    def test_schedule_appointment_schema(self):
        tool = next(t for t in TOOLS_SCHEMA if t["name"] == "schedule_appointment")
        assert tool["name"] == "schedule_appointment"
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"
        props = tool["parameters"]["properties"]
        assert "student_id" in props
        assert "advisor_name" in props
        assert "datetime_str" in props
        assert "reason" in props
        assert tool["parameters"]["required"] == ["student_id", "advisor_name", "datetime_str"]
        assert props["reason"]["type"] == "string"


class TestAcademicQueryExecution:
    """Test execute_academic_query function"""

    def test_valid_student_id(self):
        result = execute_academic_query("SV2026001")
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["student_id"] == "SV2026001"
        assert data["data"]["full_name"] == "Nguyễn Văn An"
        assert data["data"]["gpa"] == 3.85
        assert data["data"]["credits_earned"] == 118
        assert data["data"]["advisor"] == "PGS.TS Nguyễn Văn A"

    def test_case_insensitive_student_id(self):
        result = execute_academic_query("sv2026001")
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["student_id"] == "sv2026001"

    def test_invalid_student_id(self):
        result = execute_academic_query("SV9999999")
        data = json.loads(result)
        assert data["status"] == "NOT_FOUND"
        assert "Không tìm thấy" in data["message"]

    def test_empty_student_id(self):
        result = execute_academic_query("")
        data = json.loads(result)
        assert data["status"] == "NOT_FOUND"
    def test_curriculum_query_execution(self):
        result = execute_curriculum_query("AI")
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["program_code"] == "AI"
        assert data["data"]["total_credits"] == 128
        assert data["data"]["min_gpa"] == 2.0


class TestCourseCatalogQueryExecution:
    """Test execute_course_catalog_query function"""

    def test_valid_course_name_exact(self):
        result = execute_course_catalog_query("Trí tuệ nhân tạo")
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["course_code"] == "AIC201"
        assert data["data"]["name"] == "Trí tuệ nhân tạo"
        assert data["data"]["credits"] == 4
        assert data["data"]["prereq"] == ["CSI201"]

    def test_case_insensitive_course_name(self):
        result = execute_course_catalog_query("trí tuệ nhân tạo")
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["course_code"] == "AIC201"

    def test_invalid_course_name(self):
        result = execute_course_catalog_query("Môn không tồn tại")
        data = json.loads(result)
        assert data["status"] == "NOT_FOUND"
        assert "Không tìm thấy" in data["message"]


class TestScheduleAppointmentExecution:
    """Test execute_schedule_appointment function"""

    def setup_method(self):
        MOCK_APPOINTMENTS["booking_id_counter"] = 1000
        MOCK_APPOINTMENTS["bookings"] = []

    def test_valid_appointment(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="14:00 15/09/2026",
            advisor_name="PGS.TS Nguyễn Văn A",
            reason="Tư vấn tốt nghiệp"
        )
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["student_id"] == "SV2026001"
        assert data["advisor"] == "PGS.TS Nguyễn Văn A"
        assert data["datetime"] == "14:00 15/09/2026"
        assert "booking_id" in data
        assert data["booking_id"].startswith("BK-")

    def test_invalid_student(self):
        result = execute_schedule_appointment(
            student_id="SV9999999",
            datetime_str="14:00 15/09/2026",
            advisor_name="PGS.TS Nguyễn Văn A"
        )
        data = json.loads(result)
        assert data["status"] == "STUDENT_NOT_FOUND"

    def test_invalid_advisor(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="14:00 15/09/2026",
            advisor_name="Cố vấn không tồn tại"
        )
        data = json.loads(result)
        assert data["status"] == "ADVISOR_NOT_FOUND"

    def test_invalid_datetime_format(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="invalid-format",
            advisor_name="PGS.TS Nguyễn Văn A"
        )
        data = json.loads(result)
        assert data["status"] == "INVALID_DATETIME"

    def test_date_not_available(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="14:00 01/01/2027",
            advisor_name="PGS.TS Nguyễn Văn A"
        )
        data = json.loads(result)
        assert data["status"] == "DATE_NOT_AVAILABLE"

    def test_slot_not_available(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="11:00 15/09/2026",
            advisor_name="PGS.TS Nguyễn Văn A"
        )
        data = json.loads(result)
        assert data["status"] == "SLOT_NOT_AVAILABLE"

    def test_optional_reason_parameter(self):
        result = execute_schedule_appointment(
            student_id="SV2026001",
            datetime_str="14:00 15/09/2026",
            advisor_name="PGS.TS Nguyễn Văn A"
        )
        data = json.loads(result)
        assert data["status"] == "SUCCESS"
        assert data["reason"] == ""


class TestDispatchToolCall:
    """Test dispatch_tool_call router"""

    def setup_method(self):
        MOCK_APPOINTMENTS["booking_id_counter"] = 1000
        MOCK_APPOINTMENTS["bookings"] = []

    def test_dispatch_academic_query(self):
        result = dispatch_tool_call("academic_query", {"student_id": "SV2026001"})
        data = json.loads(result)
        assert data["status"] == "SUCCESS"

    def test_dispatch_course_catalog_query(self):
        result = dispatch_tool_call("course_catalog_query", {"course_name": "Trí tuệ nhân tạo"})
        data = json.loads(result)
        assert data["status"] == "SUCCESS"

    def test_dispatch_schedule_appointment(self):
        result = dispatch_tool_call("schedule_appointment", {
            "student_id": "SV2026001",
            "datetime_str": "14:00 15/09/2026",
            "advisor_name": "PGS.TS Nguyễn Văn A"
        })
        data = json.loads(result)
        assert data["status"] == "SUCCESS"

    def test_dispatch_unknown_tool(self):
        result = dispatch_tool_call("unknown_tool", {})
        data = json.loads(result)
        assert data["status"] == "UNKNOWN_TOOL"
        assert "không tồn tại" in data["error"]


class TestMockDataIntegrity:
    """Test mock data structures are complete"""

    def test_mock_students_not_empty(self):
        assert len(MOCK_STUDENTS) >= 2
        for sid, data in MOCK_STUDENTS.items():
            assert "full_name" in data
            assert "gpa" in data
            assert "credits_earned" in data
            assert "advisor" in data
            assert "completed_courses" in data

    def test_mock_advisors_not_empty(self):
        assert len(MOCK_ADVISOR_SCHEDULE) >= 2
        for name, data in MOCK_ADVISOR_SCHEDULE.items():
            assert "advisor_id" in data
            assert "availability" in data
            assert "max_appointments_per_day" in data

    def test_mock_course_catalog_not_empty(self):
        assert len(MOCK_COURSE_CATALOG) >= 10
        for code, data in MOCK_COURSE_CATALOG.items():
            assert "name" in data
            assert "credits" in data
            assert "prereq" in data
            assert "is_open" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])