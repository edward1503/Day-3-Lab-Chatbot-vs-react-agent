"""
Tool: search_attractions
Tìm các địa điểm tham quan nổi tiếng bằng Tavily Search API.

API Docs: https://docs.tavily.com/
Package: pip install tavily-python
"""

import os
import time

from dotenv import load_dotenv
from tavily import TavilyClient

from src.schemas.models import Attraction, AttractionList, ActivityType
from src.telemetry.logger import logger

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def search_attractions(
    city: str,
    activity_type: ActivityType = ActivityType.BOTH,
    max_results: int = 5,
) -> AttractionList:
    """
    Tìm kiếm địa điểm tham quan tại thành phố bằng Tavily Search API.

    Args:
        city: Tên thành phố (ví dụ: "Đà Nẵng")
        activity_type: Lọc theo loại hoạt động (indoor/outdoor/both)
        max_results: Số lượng kết quả tối đa

    Returns:
        AttractionList: Danh sách địa điểm đã parse
    """
    start_time = time.time()
    logger.log_event("TOOL_START", {
        "tool": "search_attractions",
        "city": city,
        "activity_type": activity_type.value,
        "max_results": max_results,
    })

    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        raise ValueError("Chưa cấu hình TAVILY_API_KEY trong file .env")

    # Tạo search query theo activity_type
    if activity_type == ActivityType.INDOOR:
        query = f"hoạt động trong nhà bảo tàng triển lãm mua sắm spa tại {city} đánh giá cao"
    elif activity_type == ActivityType.OUTDOOR:
        query = f"địa điểm du lịch ngoài trời biển núi công viên tại {city} đánh giá cao"
    else:
        query = f"địa điểm du lịch nổi tiếng nhất tại {city} top tham quan đánh giá cao"

    # Gọi Tavily API
    client = TavilyClient(api_key=TAVILY_API_KEY)
    results = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
    )

    # Keyword phân loại indoor / outdoor
    indoor_keywords = {"bảo tàng", "museum", "triển lãm", "gallery", "mua sắm", "shopping",
                       "spa", "chợ", "market", "nhà hàng", "quán", "café", "rạp", "karaoke"}
    outdoor_keywords = {"biển", "beach", "núi", "mountain", "công viên", "park", "hồ", "lake",
                        "thác", "waterfall", "đảo", "island", "sông", "cầu", "bridge"}

    # Parse results thành list[Attraction]
    attractions = []
    for r in results.get("results", [])[:max_results]:
        title = r.get("title", "N/A")
        content = r.get("content", "")[:300]

        # Xác định activity_type dựa trên keywords
        combined_text = (title + " " + content).lower()
        is_indoor = any(kw in combined_text for kw in indoor_keywords)
        is_outdoor = any(kw in combined_text for kw in outdoor_keywords)

        if is_indoor and not is_outdoor:
            detected_type = ActivityType.INDOOR
        elif is_outdoor and not is_indoor:
            detected_type = ActivityType.OUTDOOR
        else:
            detected_type = ActivityType.BOTH

        attraction = Attraction(
            name=title,
            activity_type=detected_type,
            description=content,
            address=None,
            rating=None,
            estimated_visit_hours=None,
            entrance_fee=None,
        )
        attractions.append(attraction)

    latency_ms = int((time.time() - start_time) * 1000)

    logger.log_event("TOOL_COMPLETE", {
        "tool": "search_attractions",
        "city": city,
        "results_count": len(attractions),
        "latency_ms": latency_ms,
    })

    return AttractionList(
        city=city,
        attractions=attractions,
        activity_filter=activity_type,
    )
