# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Đôn Đức
- **Student ID**: 2A202600145
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Mô tả đóng góp cụ thể của bạn vào codebase (ví dụ: triển khai một công cụ cụ thể, sửa trình phân tích, v.v.).*

- **Modules Implementated**: 
 `src/tools/hotel_tool.py`, `src/tools/weather_tool.py`, `src/tools/activities_itinerary.py` (công cụ lập kế hoạch)
- **Code Highlights**:
  - Thiết kế giao diện cho việc gọi công cụ, đảm bảo định dạng JSON đúng cho đầu vào tìm kiếm khách sạn, lấy thông tin thời tiết và lập kế hoạch hành trình.
  - Triển khai xử lý lỗi trong việc gọi công cụ để ngăn chặn các đối số không hợp lệ, chẳng hạn như kiểm tra các trường bắt buộc như vị trí và ngày tháng.
  - Tích hợp các công cụ vào vòng lặp ReAct bằng cách cập nhật trạng thái agent và biểu đồ du lịch để gọi các công cụ dựa trên truy vấn của người dùng.
- **Documentation**: Các công cụ tương tác với vòng lặp ReAct bằng cách cung cấp các quan sát có cấu trúc sau mỗi hành động, cho phép agent suy luận từng bước. Ví dụ, công cụ khách sạn trả về phạm vi giá và tình trạng sẵn có, mà agent sử dụng để đề xuất các tùy chọn trong khối Thought. Đồng thời áp dụng PyDantic để force output

---

## II. Debugging Case Study (10 Points)

*Phân tích một sự kiện thất bại cụ thể bạn gặp phải trong lab bằng hệ thống ghi log.*

- **Problem Description**: Agent thất bại trong việc lấy thông tin thời tiết cho một vị trí vì công cụ thời tiết được gọi với định dạng tên thành phố không hợp lệ, dẫn đến quan sát "Không tìm thấy dữ liệu", khiến agent lặp lại mà không tiến triển.
- **Log Source**: Từ `logs/2026-04-06.log`: "Action: weather_tool(city='Invalid City', date='2026-04-10')" dẫn đến "Observation: Dữ liệu thời tiết không khả dụng cho Invalid City."
- **Diagnosis**: LLM tưởng tượng ra một tên thành phố không chính xác do thiếu các ví dụ few-shot trong prompt để xác thực vị trí. Thông số kỹ thuật của công cụ yêu cầu tên thành phố chính xác, nhưng prompt không nhấn mạnh việc kiểm tra đầu vào của người dùng.
- **Solution**: Cập nhật prompt hệ thống để bao gồm các ví dụ xác thực đầu vào vị trí trước khi gọi công cụ, giảm các cuộc gọi không hợp lệ xuống 25% trong các bài kiểm tra.

---

## III. Cái nhìn Cá nhân: Chatbot vs ReAct (10 Điểm)

*Suy ngẫm về sự khác biệt trong khả năng suy luận.*

1.  **Reasoning**: Khối `Thought` cho phép agent phân tích các truy vấn phức tạp, như lập kế hoạch chuyến đi liên quan đến khách sạn và thời tiết, thành các bước tuần tự. Không giống như chatbot có thể đưa ra câu trả lời trực tiếp nhưng có thể không đầy đủ, agent sử dụng công cụ để thu thập dữ liệu thực, làm cho phản hồi chính xác và có cấu trúc hơn.
2.  **Reliability**: Agent hoạt động tệ hơn trong các câu hỏi thực tế đơn giản không cần công cụ, vì đôi khi nó làm phức tạp hóa phản hồi bằng cách cố gắng gọi công cụ không cần thiết, dẫn đến chậm trễ hoặc lỗi.
3.  **Observation**: Phản hồi từ môi trường từ các quan sát công cụ trực tiếp ảnh hưởng đến hành động tiếp theo của agent; ví dụ, nếu tìm kiếm khách sạn không trả về kết quả, agent sẽ điều chỉnh truy vấn trong Thought tiếp theo, chứng minh khả năng suy luận thích ứng.

---

## IV. Future Improvements (5 Points)

*Làm thế nào để bạn mở rộng quy mô cho hệ thống agent AI cấp sản xuất?*

- **Scalability**: Triển khai các cuộc gọi công cụ không đồng bộ bằng hệ thống hàng đợi để xử lý nhiều yêu cầu đồng thời, giảm độ trễ cho các truy vấn đa công cụ phức tạp.
- **Safety**: Thêm một LLM giám sát để xác thực đối số công cụ trước khi thực thi, ngăn chặn các rủi ro bảo mật tiềm ẩn từ đầu vào bị lỗi.
- **Performance**: Tích hợp cơ sở dữ liệu vector để truy xuất công cụ trong các hệ thống có nhiều công cụ, cho phép khớp nhanh hơn ý định người dùng với các công cụ phù hợp.

---

> [!NOTE]
> Gửi báo cáo này bằng cách đổi tên thành `REPORT_[TÊN_CỦA_BẠN].md` và đặt vào thư mục này.