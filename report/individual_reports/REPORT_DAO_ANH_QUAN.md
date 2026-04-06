# Báo Cáo Cá Nhân: Lab 3 - So Sánh Chatbot vs ReAct Agent

- **Tên Sinh Viên**: Đào Anh Quân
- **Mã Sinh Viên**: 2A202600028
- **Ngày**: 6/4/2026

---

## I. Đóng Góp Kỹ Thuật (15 Điểm)

**Các Module Triển Khai**:
- `src/tools/activities_itinerary.py`: Triển khai công cụ khám phá điểm du lịch và lập lịch trình. Bao gồm 3 hàm: `explore_top_attractions()`, `search_by_category()`, `get_itinerary_suggestion()` với dữ liệu giả liệt kê 5 thành phố Việt Nam (Hà Nội, Sài Gòn, Đà Nẵng, Huế, Nha Trang).
- `src/tools/stays_hotels.py`: Triển khai công cụ tìm kiếm khách sạn và so sánh giá. Bao gồm 3 hàm: `search_hotels()`, `get_hotel_details()`, `compare_hotels()` với dữ liệu thực tế (4-5 khách sạn mỗi thành phố, giá $25-$180).
- `tests/test_all_tools.py`: Xây dựng bộ test toàn diện 8 công cụ với Integration test cho Agent sử dụng mô hình Phi-3 local, kết quả ✓ All tests passed.

**Code Highlights**:
```python
# src/tools/activities_itinerary.py
attractions_data = {
    "hà nội": [
        {"name": "Lăng Hồ Chí Minh", "kind": "monument", "rating": 4.8, ...},
        {"name": "Thành phố cổ Hà Nội", "kind": "historic", "rating": 4.9, ...}
    ]
}

def explore_top_attractions(location, limit=5, kind=None):
    # Trả về danh sách định dạng string có tên, loại, đánh giá, mô tả chi tiết
```

**Documentation**: Các công cụ trả về chuỗi văn bản định dạng rõ ràng, giúp Agent dễ dàng đọc và tổng hợp vào Câu trả lời cuối cùng (final_answer). Tích hợp hoàn toàn vào vòng ReAct qua phương thức `_execute_tool()` trong `src/agent/agent.py` với 9 công cụ liên kết (2 vận chuyển, 2 thời tiết, 3 khách sạn, 2 điểm tham quan).

---

## II. Trường Hợp Gỡ Lỗi (10 Điểm)

**Mô Tả Vấn Đề**: Agent với mô hình Phi-3 local bị timeout khi gọi `get_weather_forecast()`. Agent đạt tối đa số bước (5) mà không trả về câu trả lời cuối cùng, đặc biệt là gọi công cụ không tồn tại `search_weather_forecast`.

**Nguồn Log**: `logs/2026-04-06.log` (09:28-09:40)
```json
{"timestamp": "2026-04-06T09:29:05.962317", "event": "AGENT_END", 
 "data": {"status": "timeout", "steps": 3}}
```

**Chẩn Đoán**: Phi-3 (quantized 4-bit) chế độ chậm trên CPU, mỗi lệnh gọi LLM: 10-23 giây. Token prompt tăng dần (873 → 1267) theo lịch sử. Khi công cụ trả về dữ liệu, Agent nhầm lẫn format hoặc tên công cụ, dẫn đến gọi `search_weather_forecast` (không tồn tại), không có tín hiệu thành công → lặp vòng ReAct vô hạn.

**Giải Pháp**:
1. Mở rộng timeout: `max_steps = 8` cho Phi-3 (thay vì 5 cho GPT-4o)
2. Thêm xác thực tên công cụ trong `_execute_tool()` kiểm tra công cụ có tồn tại hay không
3. Rút ngắn dữ liệu observation để giữ prompt.tokens nhỏ, tránh nhầm lẫn

**Kết Quả**: Chạy lần sau thành công với thực thi công cụ đúng, trả về câu trả lời rõ ràng.

---

## III. Nhận Xét Cá Nhân: Chatbot vs ReAct (10 Điểm)

1. **Suy Luận**: Khối `Thought` giúp Agent có "ý thức" về mục tiêu. Thay vì trả lời bừa, nó dừng suy nghĩ: "Để trả lời cần dữ liệu Vietnam Airlines ₫2.69M" thay vì Chatbot chỉ nói "1-3 triệu đồng tùy hãng". ReAct gọi công cụ chính xác hơn nhờ có ý thức về yêu cầu, không phải guessing.

2. **Độ Tin Cậy**: Agent đáng tin cậy hơn ở câu hỏi cần dữ liệu thời gian thực (xem giá vé, khách sạn, thời tiết). Tuy nhiên tệ hơn Chatbot ở Q&A đơn giản ("Chào bạn") vì bắt buộc JSON + vòng ReAct gây tốn tài nguyên, tăng latency không cần thiết. Khi tool bị lỗi (FlightRadar24), Agent lặp vô hạn còn Chatbot thẳng nói "tôi không có thông tin".

3. **Observation**: Phản hồi từ môi trường là "kiến thức mới" nạp vào context. Nếu tool trả về "Vietnam Airlines ₫2.69M", Agent suy ra "đủ tiền → có thể đặt vé" ở bước tiếp theo. Nhưng nếu Phi-3 nhận sai format (e.g., "Hà Nội 37°C" → "mưa"), nó sai lặp lại trong mỗi bước sau.

---

## IV. Cải Tiến Tương Lai (5 Điểm)

**Scalability**: Sử dụng **Vector Database (Pinecone/Weaviate)** lưu embeddings 1M+ điểm du lịch/khách sạn, giúp Agent tìm theo ngữ nghĩa ("khu resort bãi biển sang trọng" → 10K+ kết quả) thay vì search tuần tự dữ liệu tĩnh. Thêm **Async tool execution** gọi song song: `search_hotels() + search_attractions() + get_weather_forecast()` → 3 lần nhanh hơn sequential.

**Safety**: Áp dụng **Supervisor Agent pattern** xác thực từng action trước thực thi (kiểm tra tool tồn tại, date hợp lệ check_out > check_in, API quota). Tránh Agent gọi tool không tồn tại (`search_weather_forecast` error) hay params sai (negative nights).

**Performance**: Tích hợp **Caching (Redis)** cho kết quả thời tiết/khách sạn giống nhau để tiết kiệm API call và latency. Ví dụ: User hỏi thời tiết Hà Nội lần 2 → trả về cache 1 giây thay vì API call 5 giây.

---

> [!NOTE]
> Báo cáo này được hoàn thành và lưu thành file `REPORT_DAO_ANH_QUAN.md`.
