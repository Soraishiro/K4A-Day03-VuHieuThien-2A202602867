"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from guardrail_agent import GuardrailAgent
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Tải danh sách test cases từ config/test_cases.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu.")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer, guardrail: GuardrailAgent = None) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server.
    Tích hợp Guardrail Agent để kiểm duyệt an ninh trước khi thực thi mỗi tool call.
    Hỗ trợ đa bước: sau khi nhận Observation từ Tool, tiếp tục gọi LLM để quyết định bước tiếp theo.
    Trả về danh sách trace log của phiên thực thi.
    """
    if guardrail is None:
        guardrail = GuardrailAgent()

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    # 🛡️ Guardrail: Pre-check user query for security issues
    is_safe, safety_reason = guardrail.review_user_query(user_query)
    if not is_safe:
        print(f"[GUARDRAIL BLOCKED]: {safety_reason}")
        print(f"[FINAL ANSWER]: Tôi chỉ là trợ lý học vụ, tôi không thể giúp với yêu cầu đó.")
        return [{
            "step": 0,
            "query": user_query,
            "action_type": "GUARDRAIL_BLOCKED",
            "reason": safety_reason,
            "output": "Tôi chỉ là trợ lý học vụ, tôi không thể giúp với yêu cầu đó.",
            "latency_ms": 0
        }]

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    chat_history = []
    prev_tool_calls = []

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        # Gọi LLM với Native Tool Calling Specs và chat history
        llm_response = provider.generate_with_tools(user_query, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT, chat_history=chat_history)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")

        # Case 1: LLM trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Case 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            tool_call_id = llm_response.get("tool_call_id", f"call_{tool_name}_{step}")

            # 🛡️ Guardrail: Review tool call before execution
            approved, guardrail_reason = guardrail.review_tool_call(tool_name, arguments, user_query, chat_history)
            if not approved:
                print(f"[GUARDRAIL BLOCKED]: {guardrail_reason}")
                print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
                obs_str = json.dumps({
                    "status": "GUARDRAIL_REJECTED",
                    "message": guardrail_reason
                }, ensure_ascii=False)

                chat_history.append({
                    "role": "assistant",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "thought": thought + " [BLOCKED BY GUARDRAIL]",
                    "tool_call_id": tool_call_id
                })
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": obs_str
                })

                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "GUARDRAIL_REJECTED",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "reason": guardrail_reason,
                    "observation": {"status": "GUARDRAIL_REJECTED", "message": guardrail_reason},
                    "latency_ms": latency_ms
                })
                continue

            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            # Guardrail: Check for duplicate tool calls
            current_call_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True, ensure_ascii=False)}"
            if current_call_key in prev_tool_calls:
                print(f"⚠️ [GUARDRAIL - Duplicate]: Trùng lặp tool call - chặn gọi lại {tool_name}!")
                obs_str = json.dumps({
                    "status": "DUPLICATE_REJECTED",
                    "message": "Tool call bị trùng lặp, đã được chặn bởi guardrail"
                }, ensure_ascii=False)

                chat_history.append({
                    "role": "assistant",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "thought": thought + " [DUPLICATE_REJECTED]",
                    "tool_call_id": tool_call_id
                })
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": obs_str
                })

                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "GUARDRAIL_DUPLICATE",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": {"status": "DUPLICATE_REJECTED", "message": "Tool call blocked by guardrail"},
                    "latency_ms": latency_ms
                })
                continue
            prev_tool_calls.append(current_call_key)

            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})

            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print(f"⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng!")
                chat_history.append({
                    "role": "assistant",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "thought": thought,
                    "tool_call_id": tool_call_id
                })
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"status": "ERROR", "message": "MCP Server trả về kết quả rỗng"}, ensure_ascii=False)
                })

                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "TOOL_EXECUTION",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": {"status": "ERROR", "message": "Empty result"},
                    "latency_ms": latency_ms
                })

                final_answer = "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server."
                print(f"🧠 [Thought]: Đã nhận được dữ liệu từ MCP Server. Tổng hợp kết quả phản hồi.")
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step + 1,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
                    "output": final_answer,
                    "latency_ms": 10.0
                })
                break
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")

                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "TOOL_EXECUTION",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "observation": obs_data,
                    "latency_ms": latency_ms
                })

                chat_history.append({
                    "role": "assistant",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "thought": thought,
                    "tool_call_id": tool_call_id
                })
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": obs_str
                })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")

    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    guardrail = GuardrailAgent()

    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}")
    print(f"🛡️ Guardrail Agent: Active\n")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")

    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server, guardrail)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print(f"🚀 [TEST SUITE MODE] Kiểm tra {len(tests)} Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []

        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")

            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server, guardrail)
                all_traces.extend(logs)
                completed_count += 1

        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")

        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứng học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server, guardrail)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
