# 🧠 Kí Ức Hệ Thống: Smart Travel Agent (LangGraph + Gemini)

*File này là Memory Document, được sinh ra để tổng hợp toàn bộ context, thiết kế cơ sở hạ tầng và những cập nhật nâng cao mà Agent "Antigravity" và người dùng đã làm việc cùng nhau. Hãy nạp file này ở các phiên làm việc sau để Agent lập tức nắm bắt lại tiến độ.*

---

## 1. Bản Chất Dự Án
Đây là hệ thống **Trợ Lý Du Lịch Thông Minh**, sử dụng **LangGraph** để dàn dựng (Orchestration) quy trình, **Gemini 2.5 Flash** để suy luận (Reasoning) & tổng hợp, được hiển thị ra giao diện bằng Streaming **Gradio**. 

Hệ thống hoạt động như một Hybrid Agent, kết hợp giữa Pipeline Đa Bước cố định (Node-to-Node) và Khả năng Gọi Công Cụ tự động (Auto Tool-calling) cho các tác vụ ngắn.

---

## 2. Các Framework & Thư viện Cốt lõi
* **LLM Provider**: SDK mới nhất từ Google `google.genai` (đã bỏ hẳn bản cũ bị Deprecated `google.generativeai`).
* **Graph**: `langgraph.graph.StateGraph`
* **Giao Diện**: `gradio` với chức năng `generator` (yield từng chunk khi graph hoàn thành logic).
* **Data Parser**: `Pydantic` models.

---

## 3. Kiến Trúc Hybrid Graph (Luồng Hoạt Động)

Hệ thống có một khối não (Router) ở Node 1 (`parse_input_node`) để "Bắt Bệnh" người dùng thông qua Keyword `"intent"`, chia làm **3 hướng**:

### 🎯 Nhánh 1: Conversational (Hội thoại lẻ, Chào hỏi)
* LLM đối đáp nhẹ nhàng, hỏi thêm thông tin (VD: "Bạn dự định đi đâu và trong mấy ngày?")
* Đi thẳng qua `END`.

### ⚡ Nhánh 2: Short Query (Truy vấn nhanh)
* **Kích hoạt tính năng**: Native Function Calling (`client.chats.create` config với tools Python).
* Khi user hỏi "Thời tiết Vũng Tàu hôm nay ra sao?" hoặc "Tìm tôi cái khách sạn", Node `short_query_node` sẽ đón lấy và LLM TỰ ĐỘNG gọi chính xác 1 API đó và trả kết quả rút gọn trong một nốt nhạc, không làm phiền workflow lớn.

### 🗺️ Nhánh 3: Full Plan (Lên cấu trúc đại kế hoạch)
Khi đáp ứng đủ `Destination` & `Days`, pipeline khổng lồ khởi động:
1. `check_weather`: (OpenWeatherMap API) Check thời tiết -> Phân loại Outdoor/Indoor.
2. `ask_user_replan`: Hỏi mồi (Human-in-the-loop) "Thời tiết xấu, bạn có muốn đổi sang đi trong nhà không?".
3. `search_attractions`: (Tavily Search API) List địa điểm dựa trên Outdoor/Indoor.
4. `calculate_distances`: (Google Maps API) **[TẠM TẮT AN TOÀN DO CHƯA CÓ API_KEY]**
5. `find_hotels`: (SerpAPI) Quét Google Hotels với Budget dự tính.
6. `estimate_budget`: (Python) Tính trung bình 5 khách sạn TOP, kết hợp ước tính di chuyển x2.
7. `generate_plan`: LLM gộp tất cả viết thành 1 bài Markdown hoành tráng.
8. `summarize_agent_trace`: Đổ ra thống kê Log & Token.

---

## 4. Nhật Ký Giải Quyết Bug ("Sự cố đã Fix")
1. **Pydantic Type Casting (Gãy do ép kiểu)**: Đã viết các hàm safety (`_safe_int`, `_safe_float`) trong `parse_input`. Code không còn bị văng `ValueError` nếu LLM bắt sai số tiền "5 triệu".
2. **Quota Exceeded Error (Lỗi 429)**: Quăng lỗi bắt cụ thể thông báo *"Hết hạn mức API Key"*, không còn chèn lấp làm user nghi ngờ model xuất file JSON hỏng.
3. **Telemetry Bug**: Phân loại và show cụ thể Prompt Token + Completion Token từ biến Object trả lại thay vì biến Dict lồng ghép. Fix cả lỗi bị cộng dồn token khi chạy liên tục qua nhiều query bằng `tracker.session_metrics.clear()`.
4. **Google Maps Lỗi vì Thiếu API**: Không còn văng Traceback nữa, mà tự bypass bằng một mock node trả về mảng `distances: []`.

---

## 5. API Keys Cần Có (`.env`)
* `GEMINI_API_KEY`: Quan trọng nhất (để suy luận).
* `OPENWEATHERMAP_API_KEY`: Thời tiết.
* `TAVILY_API_KEY`: Địa điểm vui chơi.
* `SERPAPI_API_KEY`: Check khách sạn.
* `GOOGLE_MAPS_API_KEY`: Đã comment ở mức hệ thống (nếu bật lại trong graph thì mới cần xài).

--- 
*Bản báo cáo này sẽ là 'Tài sản vô giá' để bạn cấp cho các AI trong các buổi code tiếp theo, giúp chúng nó có cái nhìn xuyên thời gian, tránh 'phá' mất logic phức tạp mà ta đã xây!*
