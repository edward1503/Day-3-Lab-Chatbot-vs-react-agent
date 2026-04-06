"""
Prompt Engineering cho Travel Planning Agent.
Chứa Rules, Examples, và System Prompts cho từng bước trong pipeline.
"""

import json
from src.schemas.models import TravelRequest, TransportMode


# ============================================================
# SYSTEM PROMPT — Vai trò chính của Agent
# ============================================================

SYSTEM_PROMPT = """Bạn là một Trợ Lý Du Lịch Thông Minh (Smart Travel Planner Agent).

## Vai trò
Bạn giúp người dùng lên kế hoạch du lịch hoàn chỉnh bằng tiếng Việt. 
Bạn có quyền truy cập các công cụ: kiểm tra thời tiết, tìm địa điểm, tính khoảng cách, tìm khách sạn, và ước tính chi phí.

## Quy tắc (Rules)
1. LUÔN trả lời bằng **tiếng Việt**.
2. Khi thời tiết xấu (mưa, bão), PHẢI hỏi người dùng trước khi thay đổi kế hoạch sang hoạt động trong nhà.
3. Đưa ra gợi ý cụ thể, có số liệu rõ ràng (giá cả, khoảng cách, thời gian).
4. Kế hoạch phải nằm trong ngân sách người dùng yêu cầu.
5. Nếu ngân sách không đủ, đề xuất phương án tiết kiệm hơn thay vì từ chối.
6. Ưu tiên an toàn: cảnh báo nếu thời tiết nguy hiểm.
7. Output cuối cùng phải là kế hoạch có cấu trúc rõ ràng theo từng ngày.

## Phong cách giao tiếp
- Thân thiện, chuyên nghiệp, như một hướng dẫn viên du lịch giàu kinh nghiệm.
- Sử dụng emoji phù hợp để làm sinh động nội dung.
- Giải thích lý do cho mỗi gợi ý.
"""


PARSE_REQUEST_PROMPT = """Bạn là trợ lý du lịch thông minh. Dựa trên thông tin tin nhắn từ người dùng và lịch sử chat (nếu có), hãy phân loại ý định (intent), phản hồi và trích xuất thông tin thành dạng JSON.

## Định dạng output BẮT BUỘC (JSON chuẩn, không kèm markdown code block):
{{
    "reply": "Câu trả lời của bạn gửi cho người dùng. (Thân thiện, tự nhiên. Trả lời ngay nếu user chỉ hỏi lặt vặt. Hỏi ngược lại nếu user muốn lên lịch trình nhưng thiếu dữ kiện. Báo tin vui nếu chuẩn bị lên lịch trình.)",
    "intent": "full_plan" hoặc "short_query" hoặc "conversational",
    "destination": "tên thành phố/địa điểm" (hoặc null nếu chưa có),
    "days": số_ngày (integer, hoặc null),
    "budget": ngân_sách_VNĐ (float, hoặc null),
    "num_people": số_người (integer, mặc định lấy 1),
    "preferences": "sở thích" (hoặc null),
    "transport_mode": "driving|walking|transit|bicycling"
}}

## Quy tắc Phân loại "intent":
1. **"full_plan"**: User yêu cầu LÊN LỊCH TRÌNH/KẾ HOẠCH BÀI BẢN rõ ràng và ĐÃ CHỐT cụ thể ĐIỂM ĐẾN + SỐ NGÀY.
   - Ví dụ: "Lên kế hoạch đi Đà Lạt 3 ngày", "Đi Sapa 2 ngày 3 triệu".
2. **"short_query"**: User hỏi thẳng 1-2 CÂU HỎI NHANH để LẤY THÔNG TIN (Hỏi thời tiết, Hỏi tìm phòng khách sạn, Hỏi địa điểm) mà KHÔNG HỀ MONG MUỐN lên nguyên một bản kế hoạch dài dòng.
   - Ví dụ: "Thời tiết Hà Nội hôm nay sao?", "Tìm khách sạn ở Vũng Tàu", "Đà Nẵng có khu vui chơi nào?".
   - Lưu ý: Dù user có ghi địa điểm nhưng mục đích chỉ là hỏi lặt vặt -> Xếp vào short_query.
3. **"conversational"**: Dành cho tất cả trường hợp còn lại: Chào hỏi, rủ rê, nhờ Gợi ý chung chung do chưa chốt lịch, hay cần xin thêm thông tin do khai báo thiếu ngày/điểm đến.
   - Ví dụ: "Tôi nên đi đâu?", "Chào em", "Muốn đi Đà lạt" (thiếu số ngày -> xếp vào conversational để hỏi thêm).

## Quy tắc Trích xuất Thông tin:
- Nếu user nói "triệu" → nhân 1,000,000 (Ví dụ: "5 triệu" = 5000000). Luôn điền số nguyên/float, không điền chữ vào các trường số.
- Nếu thiếu dữ liệu nào đó, ghi nhận null.
- Mọi câu giao tiếp thông thường với người dùng PHẢI được đặt trong biến "reply".

## Lịch sử hội thoại trước đó:
{chat_history}

## Tin nhắn mới nhất của người dùng:
Input: "{user_input}"
Output:
"""


# ============================================================
# WEATHER ANALYSIS PROMPT — Phân tích thời tiết
# ============================================================

WEATHER_ANALYSIS_PROMPT = """Dựa trên dữ liệu thời tiết dưới đây, hãy đánh giá ngắn gọn bằng tiếng Việt:

## Dữ liệu thời tiết:
{weather_data}

## Yêu cầu:
1. Tóm tắt thời tiết trong 2-3 câu.
2. Đánh giá: thời tiết có phù hợp cho hoạt động ngoài trời không?
3. Nếu mưa hoặc thời tiết xấu, gợi ý nên chuyển sang hoạt động trong nhà.
4. Cảnh báo nếu có điều kiện thời tiết nguy hiểm (bão, nắng nóng cực đoan).

Trả lời ngắn gọn, rõ ràng.
"""


# ============================================================
# REPLAN PROMPT — Hỏi user khi cần thay đổi kế hoạch
# ============================================================

REPLAN_PROMPT = """⚠️ **Thông báo về thời tiết:**

Dự báo thời tiết tại **{destination}** cho biết: **{weather_condition}** 
(Nhiệt độ: {temperature}°C, Độ ẩm: {humidity}%)

{weather_detail}

🔄 **Đề xuất thay đổi:**
Tôi đề xuất chuyển sang các hoạt động **trong nhà** phù hợp hơn, bao gồm:
- Tham quan bảo tàng, triển lãm
- Khám phá ẩm thực địa phương
- Mua sắm tại trung tâm thương mại
- Trải nghiệm spa, wellness

👉 Bạn có muốn tôi **thay đổi kế hoạch sang hoạt động trong nhà** không?
(Trả lời "có" hoặc "không")
"""


# ============================================================
# FINAL PLAN PROMPT — Tổng hợp kế hoạch cuối cùng
# ============================================================

FINAL_PLAN_PROMPT = """Dựa trên tất cả thông tin đã thu thập, hãy tạo kế hoạch du lịch hoàn chỉnh bằng tiếng Việt.

## Thông tin đã thu thập:

### 🌤️ Thời tiết:
{weather_info}

### 📍 Địa điểm tham quan:
{attractions_info}

### 🚗 Khoảng cách di chuyển:
{distances_info}

### 🏨 Khách sạn:
{hotels_info}

### 💰 Chi phí ước tính:
{budget_info}

### 📋 Yêu cầu ban đầu:
- Điểm đến: {destination}
- Số ngày: {days}
- Số người: {num_people}
- Ngân sách: {budget:,.0f} VNĐ
- Sở thích: {preferences}

## Yêu cầu output:
Tạo kế hoạch du lịch chi tiết theo JSON format sau:
{{
    "destination": "tên điểm đến",
    "days": số_ngày,
    "weather_summary": "tóm tắt thời tiết",
    "recommended_activity_type": "indoor|outdoor|both",
    "attractions": [...],
    "hotel_recommendation": {{...}},
    "daily_itinerary": [
        {{
            "day_number": 1,
            "activities": ["Sáng: ...", "Trưa: ...", "Chiều: ...", "Tối: ..."],
            "meals": ["Ăn sáng: ...", "Ăn trưa: ...", "Ăn tối: ..."],
            "notes": "ghi chú nếu có"
        }}
    ],
    "budget": {{...}},
    "travel_tips": ["mẹo 1", "mẹo 2"],
    "summary": "Tóm tắt toàn bộ kế hoạch bằng tiếng Việt"
}}
"""


# ============================================================
# FEW-SHOT EXAMPLES
# ============================================================

PARSE_EXAMPLES = [
    {
        "input": "Tôi muốn đi Đà Nẵng 3 ngày, budget 5 triệu",
        "output": TravelRequest(
            destination="Đà Nẵng",
            days=3,
            budget=5_000_000,
            num_people=1,
            preferences=None,
            transport_mode=TransportMode.DRIVING,
        ),
    },
    {
        "input": "Gia đình 4 người muốn đi Phú Quốc 5 ngày, thích biển, budget 30 triệu",
        "output": TravelRequest(
            destination="Phú Quốc",
            days=5,
            budget=30_000_000,
            num_people=4,
            preferences="biển",
            transport_mode=TransportMode.DRIVING,
        ),
    },
    {
        "input": "Đi Sapa 2 ngày cuối tuần, khoảng 3tr, thích trekking",
        "output": TravelRequest(
            destination="Sapa",
            days=2,
            budget=3_000_000,
            num_people=1,
            preferences="trekking",
            transport_mode=TransportMode.DRIVING,
        ),
    },
]


# ============================================================
# HELPER: Format prompt with variables
# ============================================================

def format_parse_prompt(user_input: str, chat_history: str = "Không có") -> str:
    """Tạo prompt để parse user input thành TravelRequest."""
    return PARSE_REQUEST_PROMPT.format(user_input=user_input, chat_history=chat_history)


def format_weather_analysis(weather_data: dict) -> str:
    """Tạo prompt phân tích thời tiết."""
    return WEATHER_ANALYSIS_PROMPT.format(
        weather_data=json.dumps(weather_data, ensure_ascii=False, indent=2)
    )


def format_replan_prompt(destination: str, weather_condition: str,
                         temperature: float, humidity: int,
                         weather_detail: str = "") -> str:
    """Tạo prompt hỏi user khi cần thay đổi kế hoạch."""
    return REPLAN_PROMPT.format(
        destination=destination,
        weather_condition=weather_condition,
        temperature=temperature,
        humidity=humidity,
        weather_detail=weather_detail,
    )


def format_final_plan_prompt(
    weather_info: str,
    attractions_info: str,
    distances_info: str,
    hotels_info: str,
    budget_info: str,
    destination: str,
    days: int,
    num_people: int,
    budget: float,
    preferences: str = "Không có yêu cầu đặc biệt",
) -> str:
    """Tạo prompt tổng hợp kế hoạch cuối cùng."""
    return FINAL_PLAN_PROMPT.format(
        weather_info=weather_info,
        attractions_info=attractions_info,
        distances_info=distances_info,
        hotels_info=hotels_info,
        budget_info=budget_info,
        destination=destination,
        days=days,
        num_people=num_people,
        budget=budget,
        preferences=preferences,
    )
