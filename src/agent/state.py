"""
LangGraph State Definition cho Travel Planning Agent.
Quản lý toàn bộ dữ liệu chảy qua các node trong graph.
"""

from typing import Optional, Annotated
from typing_extensions import TypedDict

from src.schemas.models import (
    TravelRequest,
    WeatherInfo,
    Attraction,
    DistanceResult,
    HotelOption,
    BudgetBreakdown,
    TravelPlan,
    ActivityType,
)


def _merge_list(left: list, right: list) -> list:
    """Custom reducer: append new items to existing list (thay vì overwrite)."""
    if not left:
        return right or []
    if not right:
        return left
    return left + right


class TravelAgentState(TypedDict):
    """
    State trung tâm của Travel Planning Agent.
    Mỗi node trong graph đọc/ghi vào state này.

    LangGraph sẽ tự động merge state updates từ mỗi node.
    Dùng custom reducer _merge_list cho messages để append thay vì overwrite.
    """

    # ── Chat History (Gradio) ──
    messages: Annotated[list, _merge_list]

    # ── User Input ──
    user_request: str                           # Raw input từ user
    chat_history: list[dict]                    # Context lịch sử chat
    intent: str                                 # "full_plan", "short_query", "conversational"
    travel_request: Optional[TravelRequest]     # Parsed structured request

    # ── Tool Results ──
    weather: Optional[WeatherInfo]              # Kết quả check thời tiết
    attractions: list[Attraction]               # Danh sách địa điểm tìm được
    distances: list[DistanceResult]             # Khoảng cách giữa các điểm
    hotels: list[HotelOption]                   # Danh sách khách sạn
    budget: Optional[BudgetBreakdown]           # Chi tiết chi phí

    # ── Control Flow ──
    activity_type: ActivityType                 # indoor/outdoor/both — dựa trên weather
    needs_replanning: bool                      # True nếu thời tiết xấu
    user_confirmed_replan: Optional[bool]       # None=chưa hỏi, True=đồng ý, False=giữ nguyên
    waiting_for_user: bool                      # True khi đang chờ user trả lời
    current_step: str                           # Tên node hiện tại (for logging)

    # ── Final Output ──
    final_plan: Optional[TravelPlan]            # Kế hoạch du lịch hoàn chỉnh
    error: Optional[str]                        # Lỗi nếu có


def create_initial_state(user_input: str, chat_history: list = None) -> dict:
    """Tạo state khởi tạo cho một phiên planning mới."""
    return {
        "messages": [],
        "user_request": user_input,
        "chat_history": chat_history or [],
        "intent": "conversational",
        "travel_request": None,
        "weather": None,
        "attractions": [],
        "distances": [],
        "hotels": [],
        "budget": None,
        "activity_type": ActivityType.BOTH,
        "needs_replanning": False,
        "user_confirmed_replan": None,
        "waiting_for_user": False,
        "current_step": "start",
        "final_plan": None,
        "error": None,
    }
