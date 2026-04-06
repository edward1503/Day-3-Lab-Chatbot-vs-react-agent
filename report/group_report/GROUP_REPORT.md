# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Nhóm 2
- **Team Members**: Nguyễn Duy Minh Hoàng (ID: 2A202600155), [Tên Thành viên 2, ...]
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

*Brief overview of the agent's goal and success rate compared to the baseline chatbot.*

- **Success Rate**: 95% on tested scenarios (including OOD detection).
- **Key Outcome**: Hệ thống Agent ReAct có khả năng suy luận đa bước tốt hơn hẳn so với baseline chatbot. Thay vì đưa ra câu trả lời không có căn cứ, Agent có thể tra cứu giá vé máy bay thực tế (Google Flights), theo dõi chuyến bay thật (FlightRadar24) và kết hợp với dữ liệu thời tiết (Open-Meteo) để trả về lịch trình chính xác.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Luồng thực thi ReAct được triển khai thông qua một vòng lặp `while` trong `agent.py`. Agent nhận System Prompt chứa mô tả công cụ, sau đó trả về định dạng JSON (với Pydantic validate) cấu trúc `thought`, `action`, `action_input`. Nếu `action` được gọi, `_execute_tool` sẽ kích hoạt Tool và trả kết quả về `Observation` trong lịch sử để LLM suy luận tiếp. Vòng lặp dừng lại khi tìm thấy `final_answer` hoặc vượt quá `max_steps`.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_weather_forecast` | `location` (str) | Tìm kiếm dự báo thời tiết và nhiệt độ tại một địa danh cụ thể. |
| `get_air_quality` | `location` (str) | Kiểm tra chất lượng không khí (AQI, PM2.5, PM10) của một thành phố. |
| `search_flight_prices` | `origin`, `destination`, `date` | Lấy giá vé máy bay thật từ Google Flights trong một ngày cụ thể. |
| `track_flight_status`  | `flight_number` (str) | Theo dõi lộ trình chuyến bay theo thời gian thực (Real-time). |

### 2.3 LLM Providers Used
- **Primary**: OpenAI `gpt-4o`
- **Secondary (Backup)**: Xử lý cục bộ bằng Regex/Keyword logic cho trường hợp OOD đơn giản nếu LLM thất bại.

---

## 3. Telemetry & Performance Dashboard

*Analyze the industry metrics collected during the final test run.*

- **Average Latency (P50)**: ~1500ms
- **Max Latency (P99)**: ~4500ms (Khi phân tích chuỗi Action phức tạp)
- **Average Tokens per Task**: ~500 tokens (Prompt + Completion)

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*

### Case Study: Lỗi định dạng JSON và Lỗi tham số IATA
- **Input**: "Lịch bay từ Hà Nội vào Sài Gòn"
- **Observation**: Agent gọi `search_flight_prices` với `origin="Hà Nội"`, gây lõi ở phía thư viện `fast_flights` vì chỉ chấp nhận mã IATA. Hoặc LLM trả lời kèm theo Markdown block (```json) khiến `Pydantic` báo lỗi parse.
- **Root Cause**: LLM suy nghĩ giống người nên đưa toàn bộ tên địa danh thay vì mã IATA, và LLM có xu hướng tự bọc mã JSON.
- **Solution**: 
  1. Thêm chỉ thị tường minh vào **System Prompt** của Agent: "Tự động chuyển đổi tên địa danh sang mã sân bay IATA (Vd: HAN, SGN)".
  2. Xử lý làm sạch chuỗi trong mã Python `re.sub(r'```json\s*|\s*```', '', llm_output).strip()` trước khi parse JSON.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Keyword-based vs LLM-based OOD Detection
- **Diff**: Thay vì dùng mảng tĩnh `["thuốc", "code"]`, đã gọi LLM để phân tích Intents (Travel/Weather vs OOD) ngay ở Phase 0.
- **Result**: Tỉ lệ nhận diện sai chủ đề (False Positive/False Negative) giảm xuống gần như 0%. Nó có thể nhận biết và chặn ngay những câu phức tạp như "Nấu bún chả" hay "Hack Facebook".

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Chào hỏi (Giao tiếp) | Tốt | Tốt | Draw |
| Tìm giá vé thực tế | Bịa đặt giá (Hallucination) | Chính xác (Gọi Google Flights) | **Agent** |
| Câu hỏi ngoài lề (OOD) | Trả lời lan man | Từ chối một cách lịch sự | **Agent** |

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Cần làm sạch đầu vào ngăn chặn Prompt Injection, vì các prompt "hack" có thể dụ LLM trả lời bỏ qua hệ thống OOD.
- **Guardrails**: Đã thiết lập giới hạn vòng lặp `max_steps = 5` để tránh LLM rơi vào vòng lặp vô tận gây tốn chi phí token.
- **Scaling**: Nhu cầu thiết kế cấu trúc Async/Event-driven cho việc chờ API (như fetch FlightRadar24) để không làm block server main thread khi có nhiều người dùng đồng thời. Tích hợp LangGraph cho việc quản lý Follow-up, ReAct và State phức tạp hơn.
