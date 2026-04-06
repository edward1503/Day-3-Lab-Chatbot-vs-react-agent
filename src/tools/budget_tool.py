"""
Tool: estimate_budget
Tính toán chi phí du lịch: Total = Hotel + (Food × Days × People) + Transport + Activities

Đây là custom Python logic, KHÔNG gọi external API.
"""

import time
from typing import Optional

from src.schemas.models import BudgetBreakdown, Attraction
from src.telemetry.logger import logger


# ============================================================
# Bảng giá tham khảo mặc định (VNĐ)
# ============================================================

DEFAULT_FOOD_PER_DAY = 300_000      # 300k VNĐ/người/ngày (ăn bình dân)
FOOD_TIERS = {
    "budget": 200_000,              # Tiết kiệm
    "standard": 300_000,            # Trung bình
    "premium": 500_000,             # Cao cấp
}


def estimate_budget(
    hotel_price_per_night: float,
    days: int,
    num_people: int = 1,
    food_per_day: float = DEFAULT_FOOD_PER_DAY,
    transport_total: float = 0,
    attractions: Optional[list[Attraction]] = None,
    total_budget: float = 0,
) -> BudgetBreakdown:
    """
    Tính toán chi phí du lịch chi tiết.

    Công thức: Total = Hotel + (Food × Days × People) + Transport + Activities

    Args:
        hotel_price_per_night: Giá khách sạn mỗi đêm (VNĐ)
        days: Số ngày du lịch
        num_people: Số người
        food_per_day: Chi phí ăn uống mỗi ngày/người (VNĐ)
        transport_total: Tổng chi phí di chuyển (VNĐ)
        attractions: Danh sách địa điểm (để tính phí vào cổng)
        total_budget: Ngân sách tổng của user (VNĐ) — để tính remaining

    Returns:
        BudgetBreakdown: Chi tiết phân bổ ngân sách
    """
    start_time = time.time()
    logger.log_event("TOOL_START", {
        "tool": "estimate_budget",
        "hotel_price": hotel_price_per_night,
        "days": days,
        "num_people": num_people,
        "total_budget": total_budget,
    })

    # Tính chi phí khách sạn
    # Số đêm = days - 1 (3 ngày 2 đêm convention), tối thiểu 1 đêm
    nights = max(days - 1, 1)
    hotel_total = hotel_price_per_night * nights

    # Tính chi phí ăn uống
    food_total = food_per_day * days * num_people

    # Tính chi phí vé tham quan
    activities_total = 0.0
    if attractions:
        for a in attractions:
            if a.entrance_fee and a.entrance_fee > 0:
                activities_total += a.entrance_fee * num_people

    # Tính tổng
    grand_total = hotel_total + food_total + transport_total + activities_total

    # Kiểm tra ngân sách
    is_within = grand_total <= total_budget if total_budget > 0 else True
    remaining = total_budget - grand_total if total_budget > 0 else 0

    latency_ms = int((time.time() - start_time) * 1000)

    result = BudgetBreakdown(
        hotel_total=hotel_total,
        hotel_per_night=hotel_price_per_night,
        food_total=food_total,
        food_per_day=food_per_day,
        transport_total=transport_total,
        activities_total=activities_total,
        grand_total=grand_total,
        days=days,
        num_people=num_people,
        is_within_budget=is_within,
        remaining_budget=remaining,
    )

    logger.log_event("TOOL_COMPLETE", {
        "tool": "estimate_budget",
        "hotel_total": hotel_total,
        "food_total": food_total,
        "transport_total": transport_total,
        "activities_total": activities_total,
        "grand_total": grand_total,
        "is_within_budget": is_within,
        "remaining": remaining,
        "latency_ms": latency_ms,
    })

    return result
