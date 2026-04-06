"""
LangGraph Travel Planning Agent — StateGraph chính.
Orchestrate toàn bộ pipeline: Parse → Weather → Replan? → Attractions → Distance → Hotels → Budget → Plan

Sử dụng GeminiProvider hiện tại (không dùng langchain LLM).
"""

import json
import os
from datetime import datetime, timedelta
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from src.agent.state import TravelAgentState, create_initial_state
from src.schemas.models import (
    TravelRequest,
    WeatherInfo,
    Attraction,
    AttractionList,
    DistanceResult,
    HotelOption,
    HotelSearchResult,
    BudgetBreakdown,
    TravelPlan,
    DayPlan,
    ActivityType,
    TransportMode,
)
from src.prompts.prompt import (
    SYSTEM_PROMPT,
    format_parse_prompt,
    format_weather_analysis,
    format_replan_prompt,
    format_final_plan_prompt,
)
from src.tools.weather_tool import get_weather_forecast
from src.tools.attractions_tool import search_attractions
from src.tools.distance_tool import calculate_distance
from src.tools.hotel_tool import hotel_finder
from src.tools.budget_tool import estimate_budget
from src.core.gemini_provider import GeminiProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

load_dotenv()


# ============================================================
# LLM Provider — sử dụng Gemini đã config
# ============================================================

_llm_instance = None

def get_llm() -> GeminiProvider:
    """Khởi tạo GeminiProvider từ .env config (singleton)."""
    global _llm_instance
    if _llm_instance is None:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
        _llm_instance = GeminiProvider(model_name=model_name, api_key=api_key)
    return _llm_instance


def _call_llm(prompt: str, system_prompt: str = SYSTEM_PROMPT, context: str = "") -> str:
    """
    Helper: Gọi LLM và log kết quả vào telemetry.
    Returns: response text
    """
    llm = get_llm()
    logger.log_event("LLM_CALL_START", {"context": context, "prompt_length": len(prompt)})

    result = llm.generate(prompt, system_prompt=system_prompt)

    # Track metrics
    tracker.track_request(
        provider=result.get("provider", "google"),
        model=llm.model_name,
        usage=result.get("usage", {}),
        latency_ms=result.get("latency_ms", 0),
    )

    logger.log_event("LLM_CALL_COMPLETE", {
        "context": context,
        "response_length": len(result.get("content", "")),
        "latency_ms": result.get("latency_ms", 0),
        "tokens": result.get("usage", {}),
    })

    return result["content"]


def _get_travel_request(state: dict) -> TravelRequest:
    """
    Safely extract TravelRequest from state.
    LangGraph state stores Pydantic models as-is, but we handle
    both TravelRequest object and dict just in case.
    """
    tr = state.get("travel_request")
    if tr is None:
        return None
    if isinstance(tr, TravelRequest):
        return tr
    if isinstance(tr, dict):
        return TravelRequest(**tr)
    return tr


# ============================================================
# NODE FUNCTIONS — Mỗi function là 1 node trong graph
# ============================================================

def parse_input_node(state: TravelAgentState) -> dict:
    """
    Node 1: Parse user input thành TravelRequest bằng LLM.
    Nếu user hỏi chung chung, LLM trả về conversational_reply và dừng.
    """
    logger.log_event("NODE_START", {"node": "parse_input", "input": state["user_request"]})

    chat_history = state.get("chat_history", [])
    history_str = ""
    # Lấy 5 tin nhắn gần nhất để làm ngữ cảnh
    for msg in chat_history[-5:]:
        if isinstance(msg, dict):
            history_str += f"{msg.get('role', 'unknown')}: {msg.get('content', '')}\n"

    if not history_str:
        history_str = "Không có"

    prompt = format_parse_prompt(state["user_request"], chat_history=history_str)

    try:
        response_text = _call_llm(prompt, context="parse_input")

        # Extract JSON từ response (LLM có thể wrap trong markdown ```json ... ```)
        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        json_str = json_str.strip()

        # Parse JSON
        parsed = json.loads(json_str)

        # Trả lời hội thoại từ LLM
        reply_msg = parsed.get("reply")
        
        # Hàm safe parse để tránh lỗi TypeError/ValueError
        def _safe_float(val, default):
            if val is None: return default
            try: return float(str(val).replace(',', '').replace(' ', ''))
            except: return default
            
        def _safe_int(val, default):
            if val is None: return default
            try: return int(str(val).replace(',', '').replace(' ', ''))
            except: return default

        # Xử lý conversational (hỏi chung chung, xin đề xuất)
        if not parsed.get("is_enough_info") or not parsed.get("destination") or not parsed.get("days"):
            logger.log_event("NODE_INCOMPLETE", {"node": "parse_input", "reason": "conversational"})
            reply = reply_msg or "❓ Tôi cần thêm thông tin. Bạn muốn đi **đâu** và trong **bao nhiêu ngày**?"
            return {
                "travel_request": None,
                "current_step": "parse_input",
                "messages": [("assistant", reply)],
            }

        # Nếu đã đủ thông tin, parse request
        budget_val = _safe_float(parsed.get("budget"), 5_000_000)
        num_people_val = _safe_int(parsed.get("num_people"), 1)
        days_val = _safe_int(parsed.get("days"), 1)
        transport_val = parsed.get("transport_mode")
        if transport_val not in ["driving", "walking", "transit", "bicycling"]:
            transport_val = "driving"

        travel_request = TravelRequest(
            destination=str(parsed["destination"]),
            days=days_val,
            budget=budget_val,
            num_people=num_people_val,
            preferences=str(parsed.get("preferences") or "Không có yêu cầu đặc biệt"),
            transport_mode=TransportMode(transport_val),
        )

        logger.log_event("NODE_COMPLETE", {"node": "parse_input", "parsed": travel_request.model_dump()})

        # Báo cáo rằng đã nhận yêu cầu và bắt đầu làm
        start_msg = reply_msg or f"📋 Đã hiểu! Đang lên kế hoạch đi {travel_request.destination} cho {num_people_val} người..."
        start_msg += f"\n\n🔍 Đang kiểm tra thời tiết tại {travel_request.destination}..."

        return {
            "travel_request": travel_request,
            "current_step": "parse_input",
            "messages": [("assistant", start_msg)],
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Parse input failed: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower() or "resource exhausted" in error_msg.lower():
            reply_msg = "⚠️ **Lỗi API Gemini:** Key của bạn đã hết hạn mức (Quota Exceeded) hoặc bị giới hạn tốc độ. Vui lòng chờ một lát hoặc đổi API Key khác nhé!"
        else:
            reply_msg = "🤖 Xin lỗi, tôi không xử lý được thông tin này do lỗi hệ thống. Bạn có thể nói rõ hơn được không? (Ví dụ: 'Tôi muốn đi Đà Lạt 3 ngày 2 triệu')"

        return {
            "travel_request": None,
            "current_step": "parse_input",
            "error": f"Lỗi catch trong parse_input: {error_msg}",
            "messages": [("assistant", reply_msg)]
        }


def check_weather_node(state: TravelAgentState) -> dict:
    """
    Node 2: Kiểm tra thời tiết tại điểm đến.
    """
    logger.log_event("NODE_START", {"node": "check_weather"})

    travel_req = _get_travel_request(state)
    if not travel_req:
        return {"error": "Chưa có travel_request", "current_step": "check_weather"}

    try:
        weather = get_weather_forecast(city=travel_req.destination, days=travel_req.days)

        needs_replan = weather.is_rainy
        activity_type = ActivityType.INDOOR if needs_replan else ActivityType.OUTDOOR

        weather_emoji = "🌧️" if needs_replan else "☀️"
        weather_msg = (
            f"{weather_emoji} **Thời tiết tại {weather.city}:**\n"
            f"- Nhiệt độ: {weather.temperature_celsius}°C\n"
            f"- Tình trạng: {weather.condition}\n"
            f"- Độ ẩm: {weather.humidity}%\n"
            f"- {weather.forecast_summary}\n"
        )

        logger.log_event("NODE_COMPLETE", {
            "node": "check_weather",
            "is_rainy": needs_replan,
            "condition": weather.condition,
        })

        return {
            "weather": weather,
            "needs_replanning": needs_replan,
            "activity_type": activity_type,
            "current_step": "check_weather",
            "messages": [("assistant", weather_msg)],
        }

    except (ValueError, NotImplementedError) as e:
        # Tool chưa implement hoặc thiếu API key → dùng giá trị mặc định
        logger.log_event("NODE_FALLBACK", {"node": "check_weather", "reason": str(e)})
        default_weather = WeatherInfo(
            city=travel_req.destination,
            temperature_celsius=28.0,
            condition="Clear",
            humidity=70,
            is_rainy=False,
            forecast_summary=f"Thời tiết tại {travel_req.destination} đẹp, thuận lợi cho du lịch.",
        )
        return {
            "weather": default_weather,
            "needs_replanning": False,
            "activity_type": ActivityType.BOTH,
            "current_step": "check_weather",
            "messages": [("assistant",
                f"⚠️ *Chưa kết nối được OpenWeatherMap API. Sử dụng dữ liệu mặc định.*\n"
                f"☀️ Giả định thời tiết tốt tại {travel_req.destination}.\n\n"
                f"🔍 Đang tìm địa điểm tham quan..."
            )],
        }
    except Exception as e:
        logger.error(f"Weather check failed: {e}")
        return {
            "weather": None,
            "needs_replanning": False,
            "activity_type": ActivityType.BOTH,
            "current_step": "check_weather",
            "error": f"Lỗi kiểm tra thời tiết: {str(e)}",
            "messages": [("assistant", f"⚠️ Không kiểm tra được thời tiết: {str(e)}. Tiếp tục với kế hoạch ngoài trời.")],
        }


def route_by_weather(state: TravelAgentState) -> Literal["ask_user_replan", "search_attractions"]:
    """
    Conditional Edge: Quyết định đi nhánh nào dựa trên thời tiết.
    """
    if state.get("needs_replanning", False) and state.get("user_confirmed_replan") is None:
        return "ask_user_replan"
    return "search_attractions"


def ask_user_replan_node(state: TravelAgentState) -> dict:
    """
    Node 2.5: Human-in-the-loop — Hỏi user có muốn đổi kế hoạch không.
    """
    logger.log_event("NODE_START", {"node": "ask_user_replan"})

    weather = state.get("weather")
    travel_req = _get_travel_request(state)

    if weather and hasattr(weather, "condition"):
        replan_msg = format_replan_prompt(
            destination=travel_req.destination,
            weather_condition=weather.condition,
            temperature=weather.temperature_celsius,
            humidity=weather.humidity,
            weather_detail=weather.forecast_summary,
        )
    else:
        replan_msg = (
            f"⚠️ Thời tiết tại {travel_req.destination} có thể không thuận lợi.\n"
            f"Bạn có muốn chuyển sang hoạt động trong nhà không? (có/không)"
        )

    logger.log_event("NODE_WAITING", {"node": "ask_user_replan", "reason": "weather_replan"})

    return {
        "current_step": "ask_user_replan",
        "waiting_for_user": True,
        "messages": [("assistant", replan_msg)],
    }


def process_replan_response_node(state: TravelAgentState) -> dict:
    """
    Node 2.6: Xử lý response của user về việc đổi kế hoạch.
    """
    user_confirmed = state.get("user_confirmed_replan", False)

    logger.log_event("NODE_START", {"node": "process_replan_response", "user_confirmed": user_confirmed})

    if user_confirmed:
        return {
            "activity_type": ActivityType.INDOOR,
            "waiting_for_user": False,
            "current_step": "process_replan_response",
            "messages": [("assistant", "✅ Đã chuyển kế hoạch sang **hoạt động trong nhà**.\n🔍 Đang tìm địa điểm phù hợp...")],
        }
    else:
        return {
            "activity_type": ActivityType.OUTDOOR,
            "waiting_for_user": False,
            "current_step": "process_replan_response",
            "messages": [("assistant", "👍 Giữ nguyên kế hoạch **hoạt động ngoài trời**.\n🔍 Đang tìm địa điểm tham quan...")],
        }


def search_attractions_node(state: TravelAgentState) -> dict:
    """
    Node 3: Tìm địa điểm tham quan bằng Tavily Search.
    """
    logger.log_event("NODE_START", {"node": "search_attractions"})

    travel_req = _get_travel_request(state)
    activity_type = state.get("activity_type", ActivityType.BOTH)
    if isinstance(activity_type, str):
        activity_type = ActivityType(activity_type)

    try:
        result = search_attractions(
            city=travel_req.destination,
            activity_type=activity_type,
            max_results=5,
        )
        attractions = result.attractions

        # Format message
        attractions_msg = f"📍 **Địa điểm tham quan tại {travel_req.destination}** ({activity_type.value}):\n\n"
        for i, a in enumerate(attractions, 1):
            rating_str = f"⭐ {a.rating}" if a.rating else ""
            attractions_msg += f"{i}. **{a.name}** {rating_str}\n   {a.description[:150]}...\n\n"

        logger.log_event("NODE_COMPLETE", {"node": "search_attractions", "count": len(attractions)})

        return {
            "attractions": attractions,
            "current_step": "search_attractions",
            "messages": [("assistant", attractions_msg + "🚗 Đang tính khoảng cách di chuyển...")],
        }

    except (ValueError, NotImplementedError) as e:
        logger.log_event("NODE_FALLBACK", {"node": "search_attractions", "reason": str(e)})
        return {
            "attractions": [],
            "current_step": "search_attractions",
            "messages": [("assistant",
                f"⚠️ *Chưa kết nối Tavily API: {e}*\n\n"
                f"🚗 Đang tính khoảng cách..."
            )],
        }
    except Exception as e:
        logger.error(f"Search attractions failed: {e}")
        return {
            "attractions": [],
            "current_step": "search_attractions",
            "error": f"Lỗi tìm địa điểm: {str(e)}",
            "messages": [("assistant", f"⚠️ Không tìm được địa điểm: {str(e)}")],
        }


def calculate_distances_node(state: TravelAgentState) -> dict:
    """
    Node 4: Tính khoảng cách giữa các địa điểm bằng Google Maps.
    (Tạm thời vô hiệu hóa theo yêu cầu của user vì chưa có API key)
    """
    logger.log_event("NODE_START", {"node": "calculate_distances"})

    # Tạm tắt hoàn toàn chức năng gọi API Google Maps
    return {
        "distances": [],
        "current_step": "calculate_distances",
        "messages": [("assistant", "⚠️ *Bỏ qua bước tính khoảng cách (Google Maps API hiện đang được tắt).*\n🏨 Đang tìm khách sạn...")],
    }


def find_hotels_node(state: TravelAgentState) -> dict:
    """
    Node 5: Tìm khách sạn bằng SerpApi Google Hotels.
    """
    logger.log_event("NODE_START", {"node": "find_hotels"})

    travel_req = _get_travel_request(state)

    # Tính ngày check-in/check-out
    check_in = datetime.now() + timedelta(days=7)
    check_out = check_in + timedelta(days=travel_req.days)

    # Ước tính giá tối đa cho khách sạn (30% budget)
    nights = max(travel_req.days - 1, 1)
    max_hotel_budget = travel_req.budget * 0.3 / nights

    try:
        result = hotel_finder(
            city=travel_req.destination,
            check_in=check_in.strftime("%Y-%m-%d"),
            check_out=check_out.strftime("%Y-%m-%d"),
            max_price=max_hotel_budget,
            adults=travel_req.num_people,
        )
        hotels = result.hotels

        hotel_msg = f"🏨 **Khách sạn tại {travel_req.destination}:**\n\n"
        for i, h in enumerate(hotels, 1):
            rating_str = f"⭐ {h.rating}" if h.rating else ""
            hotel_msg += f"{i}. **{h.name}** {rating_str}\n   💰 {h.price_per_night:,.0f} VNĐ/đêm\n\n"

        if not hotels:
            hotel_msg += "Không tìm thấy khách sạn phù hợp trong tầm giá.\n"

        logger.log_event("NODE_COMPLETE", {"node": "find_hotels", "count": len(hotels)})

        return {
            "hotels": hotels,
            "current_step": "find_hotels",
            "messages": [("assistant", hotel_msg + "💰 Đang tính chi phí...")],
        }

    except (ValueError, NotImplementedError) as e:
        logger.log_event("NODE_FALLBACK", {"node": "find_hotels", "reason": str(e)})
        return {
            "hotels": [],
            "current_step": "find_hotels",
            "messages": [("assistant", f"⚠️ *Chưa kết nối SerpApi: {e}*\n💰 Đang tính chi phí...")],
        }
    except Exception as e:
        logger.error(f"Hotel search failed: {e}")
        return {
            "hotels": [],
            "current_step": "find_hotels",
            "error": f"Lỗi tìm khách sạn: {str(e)}",
            "messages": [("assistant", f"⚠️ Không tìm được khách sạn: {str(e)}")],
        }


def estimate_budget_node(state: TravelAgentState) -> dict:
    """
    Node 6: Tính toán chi phí bằng custom logic.
    Sử dụng giá trung bình top 5 khách sạn × số đêm, tiền ăn trung bình × số người × số ngày.
    """
    logger.log_event("NODE_START", {"node": "estimate_budget"})

    travel_req = _get_travel_request(state)
    hotels = state.get("hotels", [])
    attractions = state.get("attractions", [])
    distances = state.get("distances", [])

    # --- Tính giá khách sạn: TRUNG BÌNH top 5 (thay vì chọn rẻ nhất) ---
    if hotels:
        hotel_prices = []
        for h in hotels:
            price = h.price_per_night if hasattr(h, "price_per_night") else h.get("price_per_night", 0)
            if price > 0:
                hotel_prices.append(price)
        if hotel_prices:
            # Lấy top 5 giá thấp nhất rồi lấy trung bình
            top_prices = sorted(hotel_prices)[:5]
            hotel_price = sum(top_prices) / len(top_prices)
        else:
            hotel_price = 500_000  # Fallback
    else:
        hotel_price = 500_000  # 500k VNĐ mặc định

    # --- Tính chi phí di chuyển ---
    transport_total = 0
    if distances:
        for d in distances:
            dist_km = d.distance_km if hasattr(d, "distance_km") else d.get("distance_km", 0)
            # Giá 15,000 VNĐ/km cho taxi/grab, × 2 cho khứ hồi
            transport_total += dist_km * 15_000 * 2

    try:
        budget_result = estimate_budget(
            hotel_price_per_night=hotel_price,
            days=travel_req.days,
            num_people=travel_req.num_people,
            transport_total=transport_total,
            attractions=attractions,
            total_budget=travel_req.budget,
        )

        nights = max(travel_req.days - 1, 1)
        budget_msg = (
            f"💰 **Chi phí ước tính ({travel_req.days} ngày {nights} đêm, {travel_req.num_people} người):**\n\n"
            f"| Hạng mục | Chi tiết | Chi phí |\n"
            f"|---|---|---|\n"
            f"| 🏨 Khách sạn | {hotel_price:,.0f}/đêm × {nights} đêm | {budget_result.hotel_total:,.0f} VNĐ |\n"
            f"| 🍜 Ăn uống | {budget_result.food_per_day:,.0f}/người/ngày × {travel_req.days} ngày × {travel_req.num_people} người | {budget_result.food_total:,.0f} VNĐ |\n"
            f"| 🚗 Di chuyển | Taxi/Grab ước tính | {budget_result.transport_total:,.0f} VNĐ |\n"
            f"| 🎫 Vé tham quan | Phí vào cổng | {budget_result.activities_total:,.0f} VNĐ |\n"
            f"| **TỔNG CỘNG** | | **{budget_result.grand_total:,.0f} VNĐ** |\n\n"
        )

        if budget_result.is_within_budget:
            budget_msg += f"✅ Nằm trong ngân sách ({travel_req.budget:,.0f} VNĐ)! Còn dư: **{budget_result.remaining_budget:,.0f} VNĐ**"
        else:
            over = budget_result.grand_total - travel_req.budget
            budget_msg += f"⚠️ Vượt ngân sách ({travel_req.budget:,.0f} VNĐ) khoảng **{over:,.0f} VNĐ** — cân nhắc giảm chi phí."

        logger.log_event("NODE_COMPLETE", {"node": "estimate_budget", "total": budget_result.grand_total, "hotel_avg": hotel_price})

        return {
            "budget": budget_result,
            "current_step": "estimate_budget",
            "messages": [("assistant", budget_msg + "\n\n📝 Đang tổng hợp kế hoạch du lịch...")],
        }

    except Exception as e:
        logger.error(f"Budget estimation failed: {e}")
        return {
            "budget": None,
            "current_step": "estimate_budget",
            "error": f"Lỗi tính chi phí: {str(e)}",
            "messages": [("assistant", f"⚠️ Lỗi tính chi phí: {str(e)}\n📝 Đang tổng hợp kế hoạch...")],
        }


def generate_plan_node(state: TravelAgentState) -> dict:
    """
    Node 7 (Final): Dùng LLM tổng hợp tất cả data thành TravelPlan tiếng Việt.
    """
    logger.log_event("NODE_START", {"node": "generate_plan"})

    travel_req = _get_travel_request(state)
    weather = state.get("weather")
    attractions = state.get("attractions", [])
    distances = state.get("distances", [])
    hotels = state.get("hotels", [])
    budget = state.get("budget")

    # Format thông tin cho prompt — safely handle both objects and dicts
    def _safe_dump(obj):
        if obj is None:
            return "Không có dữ liệu"
        if hasattr(obj, "model_dump_json"):
            return obj.model_dump_json(indent=2)
        if isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False, indent=2)
        return str(obj)

    def _safe_dump_list(items):
        if not items:
            return "Không có dữ liệu"
        dumped = []
        for item in items:
            if hasattr(item, "model_dump"):
                dumped.append(item.model_dump())
            elif isinstance(item, dict):
                dumped.append(item)
            else:
                dumped.append(str(item))
        return json.dumps(dumped, ensure_ascii=False, indent=2)

    weather_info = _safe_dump(weather)
    attractions_info = _safe_dump_list(attractions)
    distances_info = _safe_dump_list(distances)
    hotels_info = _safe_dump_list(hotels)
    budget_info = _safe_dump(budget)

    # Tạo prompt tổng hợp
    prompt = format_final_plan_prompt(
        weather_info=weather_info,
        attractions_info=attractions_info,
        distances_info=distances_info,
        hotels_info=hotels_info,
        budget_info=budget_info,
        destination=travel_req.destination,
        days=travel_req.days,
        num_people=travel_req.num_people,
        budget=travel_req.budget,
        preferences=travel_req.preferences or "Không có yêu cầu đặc biệt",
    )

    try:
        plan_text = _call_llm(prompt, context="generate_plan")

        # Cố gắng parse structured output
        try:
            json_str = plan_text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            plan_data = json.loads(json_str.strip())

            activity_type_val = plan_data.get("recommended_activity_type",
                                              state.get("activity_type", "both"))
            if isinstance(activity_type_val, ActivityType):
                activity_type_val = activity_type_val.value

            final_plan = TravelPlan(
                destination=plan_data.get("destination", travel_req.destination),
                days=plan_data.get("days", travel_req.days),
                weather_summary=plan_data.get("weather_summary", "N/A"),
                recommended_activity_type=ActivityType(activity_type_val),
                attractions=[a for a in attractions if hasattr(a, "name")] if attractions else [],
                hotel_recommendation=hotels[0] if hotels and hasattr(hotels[0], "name") else None,
                daily_itinerary=[
                    DayPlan(**day) for day in plan_data.get("daily_itinerary", [])
                ],
                budget=budget if hasattr(budget, "grand_total") else None,
                travel_tips=plan_data.get("travel_tips", []),
                summary=plan_data.get("summary", ""),
            )

        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            # Nếu không parse được JSON, tạo plan đơn giản
            weather_summary = "N/A"
            if weather and hasattr(weather, "forecast_summary"):
                weather_summary = weather.forecast_summary

            at = state.get("activity_type", ActivityType.BOTH)
            if isinstance(at, str):
                at = ActivityType(at)

            final_plan = TravelPlan(
                destination=travel_req.destination,
                days=travel_req.days,
                weather_summary=weather_summary,
                recommended_activity_type=at,
                attractions=[a for a in attractions if hasattr(a, "name")] if attractions else [],
                hotel_recommendation=hotels[0] if hotels and hasattr(hotels[0], "name") else None,
                daily_itinerary=[],
                budget=budget if budget and hasattr(budget, "grand_total") else None,
                travel_tips=[],
                summary=plan_text,
            )

        # Format output đẹp cho Gradio
        final_msg = format_travel_plan_markdown(final_plan, travel_req)

        logger.log_event("NODE_COMPLETE", {"node": "generate_plan", "has_itinerary": bool(final_plan.daily_itinerary)})

        return {
            "final_plan": final_plan,
            "current_step": "generate_plan",
            "messages": [("assistant", final_msg)],
        }

    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        return {
            "current_step": "generate_plan",
            "error": f"Lỗi tạo kế hoạch: {str(e)}",
            "messages": [("assistant", f"❌ Không thể tạo kế hoạch: {str(e)}")],
        }


def summarize_agent_trace_node(state: TravelAgentState) -> dict:
    """
    Node 8 (Cuối cùng): Tổng hợp lại tất cả các bước Agent đã thực hiện.
    Hiển thị: tool nào đã gọi, search gì, API nào trả kết quả, API nào fallback.
    """
    logger.log_event("NODE_START", {"node": "summarize_agent_trace"})

    travel_req = _get_travel_request(state)
    weather = state.get("weather")
    attractions = state.get("attractions", [])
    distances = state.get("distances", [])
    hotels = state.get("hotels", [])
    budget = state.get("budget")
    needs_replan = state.get("needs_replanning", False)
    user_confirmed = state.get("user_confirmed_replan")

    md = "## 🔍 Tổng Hợp Các Bước Agent Đã Thực Hiện\n\n"
    md += "| # | Bước | Tool/API | Kết quả |\n|---|---|---|---|\n"

    step = 1

    # Step 1: Parse
    if travel_req:
        md += f"| {step} | 📋 Phân tích yêu cầu | Gemini LLM | ✅ Đích: {travel_req.destination}, {travel_req.days} ngày, {travel_req.num_people} người, budget {travel_req.budget:,.0f} VNĐ |\n"
    else:
        md += f"| {step} | 📋 Phân tích yêu cầu | Gemini LLM | ❌ Không parse được |\n"
    step += 1

    # Step 2: Weather
    if weather and hasattr(weather, "condition"):
        src = "OpenWeatherMap API"
        md += f"| {step} | 🌤️ Kiểm tra thời tiết | {src} | ✅ {weather.city}: {weather.condition}, {weather.temperature_celsius}°C, mưa={weather.is_rainy} |\n"
    else:
        md += f"| {step} | 🌤️ Kiểm tra thời tiết | OpenWeatherMap API | ⚠️ Fallback (dữ liệu mặc định) |\n"
    step += 1

    # Step 2.5: Replan?
    if needs_replan:
        decision = "Đồng ý đổi indoor" if user_confirmed else "Giữ outdoor"
        md += f"| {step} | 🔄 Hỏi thay đổi kế hoạch | Human-in-the-loop | ✅ User: {decision} |\n"
        step += 1

    # Step 3: Attractions
    if attractions:
        names = ", ".join([a.name if hasattr(a, "name") else str(a) for a in attractions[:3]])
        md += f"| {step} | 📍 Tìm địa điểm | Tavily Search API | ✅ {len(attractions)} kết quả: {names}... |\n"
    else:
        md += f"| {step} | 📍 Tìm địa điểm | Tavily Search API | ⚠️ Fallback hoặc 0 kết quả |\n"
    step += 1

    # Step 4: Distances
    if distances:
        md += f"| {step} | 🚗 Tính khoảng cách | Google Maps API | ✅ {len(distances)} tuyến đường |\n"
    else:
        md += f"| {step} | 🚗 Tính khoảng cách | Google Maps API | ⚠️ Fallback (chưa cấu hình) |\n"
    step += 1

    # Step 5: Hotels
    if hotels:
        md += f"| {step} | 🏨 Tìm khách sạn | SerpApi (Google Hotels) | ✅ {len(hotels)} khách sạn |\n"
    else:
        md += f"| {step} | 🏨 Tìm khách sạn | SerpApi (Google Hotels) | ⚠️ Fallback hoặc 0 kết quả |\n"
    step += 1

    # Step 6: Budget
    if budget and hasattr(budget, "grand_total"):
        md += f"| {step} | 💰 Tính chi phí | Custom Python Logic | ✅ Tổng: {budget.grand_total:,.0f} VNĐ |\n"
    else:
        md += f"| {step} | 💰 Tính chi phí | Custom Python Logic | ⚠️ Không tính được |\n"
    step += 1

    # Step 7: Generate Plan
    final_plan = state.get("final_plan")
    if final_plan:
        md += f"| {step} | 📝 Tổng hợp kế hoạch | Gemini LLM | ✅ Đã tạo lịch trình chi tiết |\n"
    else:
        md += f"| {step} | 📝 Tổng hợp kế hoạch | Gemini LLM | ⚠️ Không tạo được |\n"

    md += "\n"

    # Thống kê API calls
    from src.telemetry.metrics import tracker
    if tracker.session_metrics:
        total_llm_calls = len(tracker.session_metrics)
        prompt_t = sum(m.get("prompt_tokens", 0) for m in tracker.session_metrics)
        comp_t = sum(m.get("completion_tokens", 0) for m in tracker.session_metrics)
        total_tokens = sum(m.get("total_tokens", 0) for m in tracker.session_metrics)
        total_latency = sum(m.get("latency_ms", 0) for m in tracker.session_metrics)
        md += f"### 📊 Thống kê\n"
        md += f"- **Tổng LLM calls:** {total_llm_calls}\n"
        md += f"- **Tổng tokens sử dụng:** {total_tokens:,} (Prompt: {prompt_t:,} | Completion: {comp_t:,})\n"
        md += f"- **Tổng thời gian LLM:** {total_latency/1000:.1f}s\n"

    logger.log_event("NODE_COMPLETE", {"node": "summarize_agent_trace"})

    return {
        "current_step": "summarize_agent_trace",
        "messages": [("assistant", md)],
    }


# ============================================================
# HELPER: Format TravelPlan thành Markdown đẹp cho Gradio
# ============================================================

def format_travel_plan_markdown(plan: TravelPlan, request: TravelRequest) -> str:
    """Chuyển TravelPlan thành markdown đẹp."""

    md = f"# 🧳 Kế Hoạch Du Lịch {plan.destination} — {plan.days} Ngày\n\n"

    # Weather
    md += f"## 🌤️ Thời tiết\n{plan.weather_summary}\n"
    md += f"- Hoạt động đề xuất: **{plan.recommended_activity_type.value}**\n\n"

    # Attractions
    if plan.attractions:
        md += "## 📍 Địa điểm tham quan\n"
        for i, a in enumerate(plan.attractions, 1):
            rating = f" ⭐{a.rating}" if a.rating else ""
            desc = a.description[:150] if a.description else ""
            md += f"{i}. **{a.name}**{rating} — {desc}\n"
        md += "\n"

    # Hotel
    if plan.hotel_recommendation:
        h = plan.hotel_recommendation
        md += f"## 🏨 Khách sạn đề xuất\n"
        md += f"**{h.name}** — {h.price_per_night:,.0f} VNĐ/đêm"
        if h.rating:
            md += f" ⭐{h.rating}"
        md += "\n\n"

    # Daily itinerary
    if plan.daily_itinerary:
        md += "## 📅 Lịch trình chi tiết\n\n"
        for day in plan.daily_itinerary:
            md += f"### Ngày {day.day_number}\n"
            for activity in day.activities:
                md += f"- {activity}\n"
            if day.meals:
                md += f"\n🍽️ **Ăn uống:** {', '.join(day.meals)}\n"
            if day.notes:
                md += f"\n📝 *{day.notes}*\n"
            md += "\n"

    # Budget
    if plan.budget:
        b = plan.budget
        nights = max(b.days - 1, 1)
        md += "## 💰 Chi phí\n\n"
        md += "| Hạng mục | Chi phí |\n|---|---|\n"
        md += f"| 🏨 Khách sạn ({nights} đêm) | {b.hotel_total:,.0f} VNĐ |\n"
        md += f"| 🍜 Ăn uống ({b.days} ngày × {b.num_people} người) | {b.food_total:,.0f} VNĐ |\n"
        md += f"| 🚗 Di chuyển | {b.transport_total:,.0f} VNĐ |\n"
        md += f"| 🎫 Vé tham quan | {b.activities_total:,.0f} VNĐ |\n"
        md += f"| **TỔNG CỘNG** | **{b.grand_total:,.0f} VNĐ** |\n\n"

        if b.is_within_budget:
            md += f"✅ Nằm trong ngân sách! Còn dư: **{b.remaining_budget:,.0f} VNĐ**\n\n"
        else:
            md += f"⚠️ Vượt ngân sách **{abs(b.remaining_budget):,.0f} VNĐ**\n\n"

    # Tips
    if plan.travel_tips:
        md += "## 💡 Mẹo du lịch\n"
        for tip in plan.travel_tips:
            md += f"- {tip}\n"
        md += "\n"

    # Summary
    if plan.summary:
        md += f"---\n\n📌 **Tóm tắt:** {plan.summary}\n"

    return md


# ============================================================
# BUILD GRAPH — Kết nối tất cả nodes thành StateGraph
# ============================================================

def build_travel_graph() -> StateGraph:
    """
    Xây dựng LangGraph StateGraph cho Travel Planning Agent.

    Flow:
        parse_input → check_weather → [route_by_weather]
                                          ├→ ask_user_replan → END (chờ user)
                                          └→ search_attractions
        → calculate_distances → find_hotels → estimate_budget → generate_plan → END
    """

    graph = StateGraph(TravelAgentState)

    # ── Thêm nodes ──
    graph.add_node("parse_input", parse_input_node)
    graph.add_node("check_weather", check_weather_node)
    graph.add_node("ask_user_replan", ask_user_replan_node)
    graph.add_node("process_replan_response", process_replan_response_node)
    graph.add_node("search_attractions", search_attractions_node)
    graph.add_node("calculate_distances", calculate_distances_node)
    graph.add_node("find_hotels", find_hotels_node)
    graph.add_node("estimate_budget", estimate_budget_node)
    graph.add_node("generate_plan", generate_plan_node)
    graph.add_node("summarize_agent_trace", summarize_agent_trace_node)

    # ── Set entry point ──
    graph.set_entry_point("parse_input")

    # ── Kết nối edges ──
    graph.add_conditional_edges(
        "parse_input",
        lambda s: "check_weather" if s.get("travel_request") else END,
        {"check_weather": "check_weather", END: END},
    )

    graph.add_conditional_edges(
        "check_weather",
        route_by_weather,
        {
            "ask_user_replan": "ask_user_replan",
            "search_attractions": "search_attractions",
        },
    )

    graph.add_edge("ask_user_replan", END)
    graph.add_edge("process_replan_response", "search_attractions")
    graph.add_edge("search_attractions", "calculate_distances")
    graph.add_edge("calculate_distances", "find_hotels")
    graph.add_edge("find_hotels", "estimate_budget")
    graph.add_edge("estimate_budget", "generate_plan")
    graph.add_edge("generate_plan", "summarize_agent_trace")
    graph.add_edge("summarize_agent_trace", END)

    return graph


def compile_travel_graph():
    """Compile graph thành runnable app."""
    graph = build_travel_graph()
    return graph.compile()


def run_travel_agent(user_input: str) -> list:
    """
    Chạy travel agent cho một yêu cầu.
    Returns list of (role, message) tuples.
    """
    app = compile_travel_graph()
    initial_state = create_initial_state(user_input)

    all_messages = []

    for state_update in app.stream(initial_state):
        for node_name, node_state in state_update.items():
            if "messages" in node_state:
                for msg in node_state["messages"]:
                    all_messages.append(msg)

            if node_state.get("waiting_for_user"):
                return all_messages

    return all_messages
