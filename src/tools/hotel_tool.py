"""
Tool: hotel_finder
Tìm danh sách khách sạn còn phòng trong tầm giá bằng SerpApi (Google Hotels).

API Docs: https://serpapi.com/google-hotels-api
Package: pip install serpapi
"""

import os
import re
import time

from dotenv import load_dotenv
import serpapi

from src.schemas.models import HotelOption, HotelSearchResult
from src.telemetry.logger import logger

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


def _parse_price(price_str: str) -> float:
    """Parse price string thành float. Hỗ trợ VND, USD, v.v."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d.,]", "", str(price_str))
    if "." in cleaned and "," in cleaned:
        if cleaned.index(".") < cleaned.index(","):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
            cleaned = cleaned.replace(".", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", "")
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def hotel_finder(
    city: str,
    check_in: str,
    check_out: str,
    max_price: float = None,
    adults: int = 2,
    max_results: int = 5,
) -> HotelSearchResult:
    """
    Tìm kiếm khách sạn tại thành phố bằng SerpApi Google Hotels.
    """
    start_time = time.time()
    logger.log_event("TOOL_START", {
        "tool": "hotel_finder",
        "city": city,
        "check_in": check_in,
        "check_out": check_out,
        "max_price": max_price,
        "adults": adults,
    })

    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "your_serpapi_key_here":
        raise ValueError("Chưa cấu hình SERPAPI_API_KEY trong file .env")

    client = serpapi.Client(api_key=SERPAPI_API_KEY)
    
    results = client.search(
        engine="google_hotels",
        q=f"khách sạn tại {city}",
        check_in_date=check_in,
        check_out_date=check_out,
        adults=str(adults),
        currency="VND",
        gl="vn",
        hl="vi"
    )
    
    # client.search() returns a nested structure that behaves like a dictionary
    results_dict = dict(results)

    hotels = []
    for prop in results_dict.get("properties", [])[:max_results]:
        rate_info = prop.get("rate_per_night", {})
        price_str = rate_info.get("lowest") or rate_info.get("extracted_lowest") or "0"
        
        if isinstance(price_str, (int, float)):
            price = float(price_str)
        else:
            price = _parse_price(str(price_str))

        if 0 < price < 10_000:
            price = price * 25_000

        if max_price and price > max_price and price > 0:
            continue

        hotel = HotelOption(
            name=prop.get("name", "N/A"),
            price_per_night=price,
            rating=prop.get("overall_rating"),
            address=prop.get("address"),
            amenities=prop.get("amenities", []) if isinstance(prop.get("amenities"), list) else [],
            link=prop.get("link"),
        )
        hotels.append(hotel)

    hotels.sort(key=lambda h: h.price_per_night if h.price_per_night > 0 else float("inf"))

    latency_ms = int((time.time() - start_time) * 1000)

    logger.log_event("TOOL_COMPLETE", {
        "tool": "hotel_finder",
        "city": city,
        "results_count": len(hotels),
        "cheapest_price": hotels[0].price_per_night if hotels else None,
        "latency_ms": latency_ms,
    })

    return HotelSearchResult(
        city=city,
        check_in=check_in,
        check_out=check_out,
        hotels=hotels,
    )
