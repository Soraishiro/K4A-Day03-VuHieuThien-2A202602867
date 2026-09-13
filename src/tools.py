"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: academic_query - Tra cứu hồ sơ học vụ
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ học vụ của sinh viên VinUni: GPA, số tín chỉ đã tích lũy, môn đã học, cố vấn, lịch thi.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Mã sinh viên (VD: 'SV2026001')"}
            },
            "required": ["student_id"]
        }
    },

    # Tool 2: course_catalog_query - Tra cứu thông tin môn học
    {
        "name": "course_catalog_query",
        "description": "Tra cứu thông tin môn học trong catalog VinUni: số tín chỉ, môn tiên quyết, mô tả, trạng thái mở.",
        "parameters": {
            "type": "object",
            "properties": {
                "course_name": {"type": "string", "description": "Tên môn học (VD: 'Trí tuệ nhân tạo')"}
            },
            "required": ["course_name"]
        }
    },

    # Tool 3: schedule_appointment - Đặt lịch tư vấn
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch tư vấn học vụ với Cố vấn. Kiểm tra availability trước khi booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string", "description": "Mã sinh viên"},
                "advisor_name": {"type": "string", "description": "Tên cố vấn"},
                "datetime_str": {"type": "string", "description": "Thời gian: 'HH:MM DD/MM/YYYY'"},
                "reason": {"type": "string", "description": "Lý do tư vấn (optional)"}
            },
            "required": ["student_id", "advisor_name", "datetime_str"]
        }
    },

    # Tool 4: curriculum_query - Tra cứngy chương trình đào tạo và điều kiện tốt nghiệp
    {
        "name": "curriculum_query",
        "description": "Tra cứu thông tin chương trình đào tạo và điều kiện tốt nghiệp của một chương trình (VD: 'AI').",
        "parameters": {
            "type": "object",
            "properties": {
                "program_code": {"type": "string", "description": "Mã chương trình (VD: 'AI')"}
            },
            "required": ["program_code"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_STUDENTS = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "program": "AI",
        "gpa": 3.85,
        "credits_earned": 118,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A",
        "completed_courses": ["CSI101", "CSI201", "MTH201", "AIC201", "AIC301"],
        "exam_schedule": [
            {"course": "AIC401 - Xử lý ngôn ngữ tự nhiên", "date": "20/09/2026", "time": "09:00", "room": "A101"},
            {"course": "AIC501 - Các kĩ thuật học sâu và ứng dụng", "date": "22/09/2026", "time": "14:00", "room": "B202"}
        ]
    },

    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "program": "AI",
        "gpa": 3.60,
        "credits_earned": 128,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B",
        "completed_courses": [
            "CSI101", "CSI102", "CSI201", "CSI202",
            "MTH101", "MTH201", "MTH301",
            "AIC201", "AIC301", "AIC501"
        ],
        "exam_schedule": []
    }
}

MOCK_ADVISOR_SCHEDULE = {
    "PGS.TS Nguyễn Văn A": {
        "advisor_id": "ADV001",
        "email": "nguyen.van.a@vinuni.edu.vn",
        "department": "Khoa Khoa học Máy tính VinUni",
        "availability": [
            {"date": "15/09/2026", "slots": ["09:00", "10:00", "14:00", "15:00", "16:00"]},
            {"date": "16/09/2026", "slots": ["09:00", "10:00", "11:00"]},
            {"date": "17/09/2026", "slots": ["14:00", "15:00", "16:00"]},
            {"date": "18/09/2026", "slots": ["09:00", "10:00", "14:00"]}
        ],
        "max_appointments_per_day": 5,
        "appointment_duration_minutes": 60
    },
    "TS. Lê Thị B": {
        "advisor_id": "ADV002",
        "email": "le.thi.b@vinuni.edu.vn",
        "department": "Khoa Khoa học Máy tính VinUni",
        "availability": [
            {"date": "15/09/2026", "slots": ["09:00", "11:00", "14:00"]},
            {"date": "16/09/2026", "slots": ["10:00", "14:00", "15:00"]}
        ],
        "max_appointments_per_day": 4,
        "appointment_duration_minutes": 45
    }
}

MOCK_APPOINTMENTS = {
    "booking_id_counter": 1000,
    "bookings": []
}

MOCK_COURSE_CATALOG = {
    "CSI101": {"name": "Nhập môn lập trình", "credits": 4, "prereq": [], "is_open": True,
               "summary": "Kiến thức nền tảng về máy tính, tư duy và kỹ năng lập trình."},
    "CSI102": {"name": "Lập trình hướng đối tượng", "credits": 4, "prereq": ["CSI101"], "is_open": True,
               "summary": "OOP, kế thừa, đa hình, design patterns cơ bản."},
    "CSI201": {"name": "Cấu trúc dữ liệu và giải thuật", "credits": 4, "prereq": ["CSI101"], "is_open": True,
               "summary": "Giải thuật, cấu trúc dữ liệu và phân tích độ phức tạp."},
    "CSI202": {"name": "Hệ điều hành", "credits": 4, "prereq": ["CSI201"], "is_open": True,
               "summary": "Quản lý tiến trình, bộ nhớ, hệ thống file, đồng bộ hóa."},
    "MTH101": {"name": "Toán rời rạc", "credits": 3, "prereq": [], "is_open": True,
               "summary": "Logic, tập hợp, đồ thị, tổ hợp, xác suất."},
    "MTH201": {"name": "Xác suất thống kê", "credits": 3, "prereq": ["MTH101"], "is_open": True,
               "summary": "Phân phối xác suất, kiểm định giả thuyết, hồi quy."},
    "MTH301": {"name": "Tối ưu hóa", "credits": 3, "prereq": ["MTH201"], "is_open": True,
               "summary": "Linear programming, gradient descent, convex optimization."},
    "AIC201": {"name": "Trí tuệ nhân tạo", "credits": 4, "prereq": ["CSI201"], "is_open": True,
               "summary": "Lịch sử AI, thuật giải heuristic, tìm kiếm, biểu diễn tri thức."},
    "AIC301": {"name": "Máy học", "credits": 4, "prereq": ["MTH201"], "is_open": True,
               "summary": "Hồi quy, phân lớp, gom cụm, đánh giá mô hình."},
    "AIC401": {"name": "Xử lý ngôn ngữ tự nhiên", "credits": 4, "prereq": ["AIC201"], "is_open": True,
               "summary": "CFG, DCG, FSA và các kỹ thuật xử lý văn bản."},
    "AIC501": {"name": "Các kĩ thuật học sâu và ứng dụng", "credits": 3, "prereq": ["AIC301"], "is_open": True,
               "summary": "Deep Learning, CNN, ứng dụng nhận dạng và phát hiện đối tượng."},
    "AIC601": {"name": "Học máy thống kê", "credits": 4, "prereq": ["MTH201"], "is_open": True,
               "summary": "Học có giám sát, không giám sát, học từ dữ liệu."}
}

MOCK_CURRICULUM = {
    "AI": {
        "name": "Cử nhân Trí tuệ Nhân tạo",
        "total_credits": 128,
        "min_gpa": 2.0,
        "breakdown": {
            "general": 45,
            "foundation": 57,
            "major_elective": 8,
            "interdisciplinary": 8,
            "graduation": 10
        }
    }
}


def execute_curriculum_query(program_code: str) -> str:
    """Thực thi tra cứu thông tin chương trình đào tạo và điều kiện tốt nghiệp"""
    program = MOCK_CURRICULUM.get(program_code.strip().upper())
    if program:
        return json.dumps({
            "status": "SUCCESS",
            "program_code": program_code,
            "data": program
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy chương trình '{program_code}' trong curriculum"
        }, ensure_ascii=False)


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_STUDENTS.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_course_catalog_query(course_name: str) -> str:
    """Thực thi tra cứu thông tin môn học trong catalog"""
    course_key = None
    for key, value in MOCK_COURSE_CATALOG.items():
        if value["name"].lower() == course_name.lower():
            course_key = key
            break
    
    if course_key:
        course = MOCK_COURSE_CATALOG[course_key]
        return json.dumps({
            "status": "SUCCESS",
            "course_code": course_key,
            "data": course
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy môn học '{course_name}' trong catalog"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str, reason: str = "") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    student = MOCK_STUDENTS.get(student_id.strip().upper())
    if not student:
        return json.dumps({
            "status": "STUDENT_NOT_FOUND",
            "message": f"Không tìm thấy sinh viên '{student_id}'"
        }, ensure_ascii=False)
    
    advisor = MOCK_ADVISOR_SCHEDULE.get(advisor_name)
    if not advisor:
        return json.dumps({
            "status": "ADVISOR_NOT_FOUND",
            "message": f"Không tìm thấy cố vấn '{advisor_name}'"
        }, ensure_ascii=False)
    
    try:
        time_part, date_part = datetime_str.split(" ")
        day, month, year = date_part.split("/")
        date_key = f"{day}/{month}/{year}"
    except ValueError:
        return json.dumps({
            "status": "INVALID_DATETIME",
            "message": "Định dạng datetime_str không hợp lệ. VD: '14:00 15/09/2026'"
        }, ensure_ascii=False)
    
    existing_booking = next(
        (b for b in MOCK_APPOINTMENTS["bookings"]
         if b["student_id"] == student_id.strip().upper()
         and b["advisor"] == advisor_name
         and b["date"] == date_key
         and b["time"] == time_part),
        None
    )
    if existing_booking:
        return json.dumps({
            "status": "DUPLICATE_BOOKING",
            "booking_id": existing_booking["booking_id"],
            "message": f"Lịch hẹn đã được đặt trước đó với mã {existing_booking['booking_id']} cho sinh viên {student['full_name']} với {advisor_name} vào lúc {datetime_str}."
        }, ensure_ascii=False)
    
    date_availability = next((d for d in advisor["availability"] if d["date"] == date_key), None)
    if not date_availability:
        return json.dumps({
            "status": "DATE_NOT_AVAILABLE",
            "message": f"Cố vấn {advisor_name} không có lịch làm việc vào ngày {date_key}"
        }, ensure_ascii=False)
    
    if time_part not in date_availability["slots"]:
        return json.dumps({
            "status": "SLOT_NOT_AVAILABLE",
            "message": f"Khung giờ {time_part} ngày {date_key} không còn trống"
        }, ensure_ascii=False)
    
    day_bookings = [b for b in MOCK_APPOINTMENTS["bookings"] if b["date"] == date_key and b["advisor"] == advisor_name]
    if len(day_bookings) >= advisor["max_appointments_per_day"]:
        return json.dumps({
            "status": "MAX_BOOKINGS_REACHED",
            "message": f"Cố vấn {advisor_name} đã đủ số lượng lịch hẹn tối đa cho ngày {date_key}"
        }, ensure_ascii=False)
    
    MOCK_APPOINTMENTS["booking_id_counter"] += 1
    booking_id = f"BK-{MOCK_APPOINTMENTS['booking_id_counter']}"
    
    MOCK_APPOINTMENTS["bookings"].append({
        "booking_id": booking_id,
        "student_id": student_id,
        "student_name": student["full_name"],
        "advisor": advisor_name,
        "date": date_key,
        "time": time_part,
        "reason": reason
    })
    
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": booking_id,
        "student_id": student_id,
        "student_name": student["full_name"],
        "advisor": advisor_name,
        "datetime": datetime_str,
        "reason": reason,
        "message": f"Đặt lịch thành công cho sinh viên {student['full_name']} ({student_id}) với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "course_catalog_query": execute_course_catalog_query,
    "schedule_appointment": execute_schedule_appointment,
    "curriculum_query": execute_curriculum_query
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)