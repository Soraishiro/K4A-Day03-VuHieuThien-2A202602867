# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Vũ Hiếu Thiên
> **Mã Sinh Viên / Mã Học viên:** 2A202602867
> **Chủ đề Lựa chọn:** AI Academic Assistant — Tra cứu thông tin sinh viên, chương trình đào tạo, điều kiện tốt nghiệp, đặt lịch tư vấn học vụ

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá           | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| :-------------------------- | :------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Multi-step Reasoning** |     5 / 5      | Nghiệp vụ đòi hỏi chuỗi quyết định nhiều tầng. Ví dụ điển hình ở N4: để trả lời "em đã đủ tốt nghiệp chưa?", trợ lý phải (1) lấy hồ sơ sinh viên, (2) lấy yêu cầu tốt nghiệp của chương trình, (3) đối chiếu từng khối kiến thức (tín chỉ, GPA, môn bắt buộc), (4) tổng hợp kết luận "còn thiếu X". Ở N5, trợ lý phải (1) tra môn tiên quyết của môn đích, (2) tra danh sách môn đã học của sinh viên, (3) so khớp hai tập hợp, (4) kết luận đủ/thiếu. Đây là reasoning đa tầng, không thể trả lời bằng 1 câu tra cứu đơn. |
| **2. Tool Interaction**     |     5 / 5      | Bản chất nghiệp vụ là tổng hợp từ 3 nguồn dữ liệu độc lập: hồ sơ sinh viên (thay đổi hàng ngày), chương trình đào tạo (cập nhật mỗi năm), và hệ thống đặt lịch. Không nguồn nào nằm trong "kiến thức chung" của LLM. Đặc biệt N6 buộc trợ lý phải gọi cả hai nguồn tra cứu trong cùng một câu hỏi để đối chiếu thông tin user cung cấp với thực tế. Nếu thiếu tool, không cách nào trả lời trung thực.không?                                                                                                               |
| **3. Dynamic Decision**     |     5 / 5      | Hành vi của trợ lý thay đổi theo kết quả quan sát được. N7: khi hồ sơ trả "không tìm thấy", trợ lý không được tiếp tục đặt lịch — đây là guardrail động. N5: nếu môn tiên quyết chưa có trong hồ sơ, kết luận là "chưa đủ", nhưng nếu có, kết luận đảo ngược. N6: nếu thông tin user khớp dữ liệu, trả lời bình thường; nếu mâu thuẫn, phải đính chính. Cùng một câu hỏi bề ngoài giống nhau có thể ra kết quả khác hẳn tùy dữ liệu trả về. không?                                                                         |
| **4. Long Horizon Goal**    |     4 / 5      | N6 là ví dụ mạnh nhất: user cung cấp thông tin sai (môn 3 tín chỉ, không cần môn trước) và muốn trợ lý xác nhận. Trợ lý phải giữ mục tiêu "tư vấn đúng", không bị user dẫn dắt sang mục tiêu "xác nhận user đúng". Đây là dạng "đối mặt với thông tin gây nhiễu" — một dạng long-horizon reasoning. Tuy nhiên nghiệp vụ không đòi hỏi duy trì state qua nhiều phiên (không có memory dài hạn, không có planning nhiều tuần), nên chưa đạt mức tối đa 5. không?                                                             |
| **TỔNG ĐIỂM AGENTIC FIT**   |  **19 / 20**   | Rất phù hợp để triển khai ReAct Agent. Vượt xa ngưỡng 12/20; nằm trong nhóm nghiệp vụ mà Chatbot thất bại chắc chắn.                                                                                                                                                                                                                                                                                                                                                                                                       |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

### Đoạn trích: TC07 — Multi-step reasoning với contradiction (2 tool calls → Final Answer)

TC07 là test case tiêu biểu nhất: User cung cấp thông tin sai (3 tín chỉ, không có môn tiên quyết) và Agent phải thực hiện chuỗi ReAct đa bước để đính chính.

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {"student_id": "SV2026001"},
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85,
        "credits_earned": 118,
        "completed_courses": ["CSI101", "CSI201", "MTH201", "AIC201", "AIC301"]
      }
    },
    "latency_ms": 3638.2
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "course_catalog_query",
    "arguments": {"course_name": "Trí tuệ nhân tạo"},
    "observation": {
      "status": "SUCCESS",
      "course_code": "AIC201",
      "data": {
        "name": "Trí tuệ nhân tạo",
        "credits": 4,
        "prereq": ["CSI201"],
        "is_open": true
      }
    },
    "latency_ms": 1008.8
  },
  {
    "step": 3,
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Bạn đã hoàn thành môn tiên quyết 'CSI201', vì vậy bạn đủ điều kiện để đăng ký môn 'Trí tuệ nhân tạo' (4 tín chỉ). Lưu ý: thông tin bạn nghe nói về 3 tín chỉ và không có môn tiên quyết là không chính xác.",
    "latency_ms": 3378.89
  }
]
```

### Tóm tắt toàn bộ trace (14 sự kiện / 7 test cases):

| Test Case | Loại | Tool Calls | Bước cuối | Trạng thái |
|-----------|------|-----------|-----------|------------|
| TC01 | direct_query | 0 (text only) | Final Answer | ✅ Pass |
| TC02 | single_tool_query | 1 (academic_query) | Observation → Final Answer | ✅ Pass |
| TC03 | appointment_booking | 1 (schedule_appointment) | Observation → Final Answer | ✅ Pass |
| TC04 | multi_step_reasoning | 1 (academic_query) | Final Answer với graduation check | ✅ Pass |
| TC05 | edge_case_handling | 1 (academic_query → NOT_FOUND) | Final Answer không gọi tool tiếp | ✅ Pass |
| TC06 | multi_step_reasoning | 1 (course_catalog_query) | Final Answer | ✅ Pass |
| TC07 | contradiction + noise | 2 (academic_query → course_catalog_query) | Final Answer đính chính | ✅ Pass |

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật (`OPENAI_API_KEY`) trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (OpenAI gpt-4o-mini).
- **Tổng số Test Cases đã chạy thành công:** 7 / 7 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 6 lượt (academic_query: 3, course_catalog_query: 2, schedule_appointment: 1).
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
