# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Duy Minh Hoàng
- **Student ID**: 2A202600155
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: 
  - `src/tools/transportation.py` (Tính năng tìm kiếm chuyến bay và theo dõi trạng thái chuyến bay thực tế)
  - `src/tools/weather_safety.py` (Tính năng kiểm tra chất lượng không khí / ô nhiễm)
- **Code Highlights**:
  - Tích hợp **Google Flights** thông qua `fast_flights` để lấy giá vé máy bay.
  - Tích hợp **FlightRadar24API** để theo dõi (tracking) tàu bay trên bản đồ theo thời gian thực dựa vào số hiệu chuyến bay.
  - Sử dụng **Open-Meteo Air Quality API** để lấy chỉ số ô nhiễm không khí (AQI), PM10, PM2.5 dựa trên tọa độ địa lý.
- **Documentation**: 
  - Các công cụ được tôi đóng gói trong cấu trúc chuẩn của dự án để truyền vào ReAct vòng lặp (ReAct loop).
  - Tên mô tả và danh sách tham số (parameters) của công cụ được cấu hình để LLM trong Agent có thể phân tích cú pháp (parse JSON) và gọi một cách dễ dàng, ví dụ như tự động lấy mã IATA sân bay để gọi `search_flight_prices`.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: LLM gọi công cụ `get_air_quality` nhưng bị bỏ sót chuyển đổi tọa độ, hoặc khi gọi `search_flight_prices` LLM vô tình truyền vào tên Thành phố (Ví dụ: "Hà Nội") thay vì truyền đúng định dạng mã IATA mà thư viện fast_flights yêu cầu.
- **Log Source**: 
  ```json
  {"timestamp": "2026-04-06T09:20:22.764786", "event": "AGENT_STEP", "data": {"thought": "Khong co IATA", "action": "search_flight_prices", "action_input": {"origin": "Hà Nội", "destination": "Sài Gòn", "date": "2026-04-07"}}}
  ```
- **Diagnosis**: Prompt không quy định chặt chẽ cách chuyển đổi dữ liệu đầu vào. Do LLM suy đoán tên thành phố là đủ, nên đã gây lỗi đầu vào dữ liệu API (API yêu cầu mã IATA).
- **Solution**: Cập nhật lại System Prompt cho hệ thống (trong file `agent.py`) để thêm luật cứng: `Tự động chuyển đổi tên địa danh sang mã sân bay IATA (Vd: HAN, SGN) khi gọi các công cụ tìm kiếm máy bay`. Thêm tiện ích `get_coordinates` ở `weather_safety.py` để tự phân giải tên địa điểm thành toạ độ cho API thời tiết.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` giúp mô phỏng luồng suy luận của người thật. Lúc này Chatbot không cố gắng trả lời bịa đặt (hallucinate) một chuyến bay không có thật mà nó hiểu rằng nó chưa có thông tin, và phải dùng `Action` để thực thi Tool trước khi chốt lại câu trả lời cuối cùng (`Final Answer`).
2.  **Reliability**: Trong các trường hợp hỏi cung cấp thông tin chung mang tính sáng tạo (VD: "Viết thiệp chúc mừng đi chơi"), việc đi qua Agent ReAct gây ra độ trễ cao và đôi khi thừa thãi hơn so với Chatbot thông thường vì nó cố gắng tìm công cụ thích hợp để xử lý dù không cần thiết.
3.  **Observation**: Dữ liệu từ Observation giúp LLM biết được việc gọi API có thành công hay không (VD: FlightRadar24 trả về None). Nếu thất bại, Agent tự phân tích dựa vào `Thought` ở turn tiếp theo và thông báo đàng hoàng với trình bày dễ hiểu cho User thay vì văng Exception.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Triển khai kiến trúc **Event-Driven** để xử lý các tool cần thời gian tải lâu (như tracking máy bay thời gian thực).
- **Safety**: Sử dụng cơ chế phân loại đầu vào (OOD Detection bằng LLM) để chặn những truy vấn nằm ngoài miền du lịch & thời tiết, hạn chế tài nguyên rác.
- **Performance**: Xây dựng **Cache** cho các API. Ví dụ với `get_air_quality` có thể lưu kết quả trong bộ nhớ tạm (như Redis) theo từng Thành phố trong khoảng 1 giờ để truy xuất ngay lập tức ở lần gọi sau mà không cần Fetch lại API.
