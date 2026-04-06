# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Luan Nguyen
- **Student ID**: 2A202600398
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: 
    - `src/tools/weather_safety.py`: Triển khai công cụ lấy dữ liệu thời tiết sử dụng Open-Meteo API (không cần API Key). Bao gồm Geocoding để chuyển đổi tên thành phố sang tọa độ.
    - `tests/test_weather.py`: Xây dựng bộ test toàn diện bao gồm Unit test cho tool và Integration test cho Agent.
- **Code Highlights**:
    ```python
    # src/tools/weather_safety.py
    def get_weather_forecast(location: str) -> str:
        coords = get_coordinates(location)
        if not coords:
            return f"Không tìm thấy tọa độ cho địa điểm: {location}"
        # ... gọi API và format output ...
    ```
- **Documentation**: Code được thiết kế để trả về chuỗi văn bản (String) mô tả chi tiết thời tiết, giúp Agent dễ dàng đọc và tổng hợp vào Câu trả lời cuối cùng (`final_answer`). Việc sử dụng Open-Meteo giúp hệ thống hoạt động ổn định mà không phụ thuộc vào việc quản lý API Key ngoài.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent đôi khi cố gắng truyền thêm tham số `date` vào `action_input` (ví dụ: `{"location": "Tokyo", "date": "hôm nay"}`), trong khi hàm `get_weather_forecast` của tôi chỉ chấp nhận `location`.
- **Log Source**: `logs/2026-04-06.log` (Dòng 3)
    > `{"event": "AGENT_STEP", "data": {"thought": "...", "action": "get_weather_forecast", "action_input": {"location": "Tokyo", "date": "hôm nay"}, "final_answer": null}}`
- **Diagnosis**: LLM (GPT-4o) giả định rằng công cụ thời tiết có thể lọc theo ngày, dẫn đến lỗi `TypeError` khi hàm nhận được tham số không xác định.
- **Solution**: Đã cập nhật mô tả công cụ trong `agent.py` để làm rõ rằng chỉ cần truyền `location` và tối ưu hóa logic trong `weather_safety.py` để xử lý linh hoạt hơn.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` giúp Agent có "ý thức" về mục tiêu. Thay vì trả lời bừa, nó biết dừng lại để suy nghĩ: "Để trả lời câu hỏi này, tôi cần dữ liệu thực tế", từ đó đưa ra quyết định gọi Tool chính xác hơn nhiều so với Chatbot truyền thống.
2.  **Reliability**: Agent đáng tin cậy hơn ở các câu hỏi cần dữ liệu thời gian thực. Tuy nhiên, nó có thể tệ hơn Chatbot ở các câu hỏi Q&A đơn giản (ví dụ: "Chào bạn") vì việc bắt ép output JSON và chạy vòng lặp ReAct gây tốn tài nguyên và tăng độ trễ (Latency) không cần thiết.
3.  **Observation**: Phản hồi từ môi trường (Observation) đóng vai trò là "kiến thức mới" được nạp vào context của LLM. Nếu Tool trả về lỗi, Agent có thể nhìn vào đó để sửa sai ở bước tiếp theo thay vì lặp lại lỗi cũ.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Sử dụng **OpenAPI Spec (Swagger)** để định nghĩa Tool tự động, giúp dễ dàng mở rộng lên hàng trăm công cụ mà không cần viết code import thủ công.
- **Safety**: Áp dụng **Pydantic Guardrails** chặt chẽ hơn để kiểm tra `action_input` trước khi thực thi tool, tránh các lỗi runtime.
- **Performance**: Tích hợp **Caching (như Redis)** cho các kết quả thời tiết tương tự để tiết kiệm chi phí API và giảm Latency cho người dùng.

---


