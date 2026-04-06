"""
Tool: calculate_distance
Tính khoảng cách và thời gian di chuyển bằng Google Maps Distance Matrix API.

API Docs: https://developers.google.com/maps/documentation/distance-matrix
Package: pip install googlemaps
"""

import os
import time

import googlemaps
from dotenv import load_dotenv

from src.schemas.models import DistanceResult, TransportMode
from src.telemetry.logger import logger

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def calculate_distance(
    origin: str,
    destination: str,
    mode: TransportMode = TransportMode.DRIVING,
) -> DistanceResult:
    """
    Tính khoảng cách và thời gian di chuyển giữa 2 điểm.

    Args:
        origin: Điểm xuất phát (ví dụ: "Sân bay Đà Nẵng")
        destination: Điểm đến (ví dụ: "Bà Nà Hills, Đà Nẵng")
        mode: Phương tiện di chuyển

    Returns:
        DistanceResult: Khoảng cách (km) và thời gian (phút)
    """
    start_time = time.time()
    logger.log_event("TOOL_START", {
        "tool": "calculate_distance",
        "origin": origin,
        "destination": destination,
        "mode": mode.value,
    })

    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "your_google_maps_key_here":
        raise ValueError("Chưa cấu hình GOOGLE_MAPS_API_KEY trong file .env")

    # Khởi tạo Google Maps client
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

    # Gọi Distance Matrix API
    result = gmaps.distance_matrix(
        origins=[origin],
        destinations=[destination],
        mode=mode.value,
        units="metric",
        language="vi",
    )

    # Parse response
    element = result["rows"][0]["elements"][0]

    if element["status"] != "OK":
        error_msg = f"Không thể tính khoảng cách: {element['status']}"
        logger.log_event("TOOL_ERROR", {
            "tool": "calculate_distance",
            "error": error_msg,
            "status": element["status"],
        })
        raise ValueError(error_msg)

    distance_km = element["distance"]["value"] / 1000  # meters → km
    duration_min = element["duration"]["value"] / 60    # seconds → minutes

    latency_ms = int((time.time() - start_time) * 1000)

    distance_result = DistanceResult(
        origin=origin,
        destination=destination,
        distance_km=round(distance_km, 1),
        duration_minutes=round(duration_min, 1),
        mode=mode,
    )

    logger.log_event("TOOL_COMPLETE", {
        "tool": "calculate_distance",
        "origin": origin,
        "destination": destination,
        "distance_km": distance_result.distance_km,
        "duration_min": distance_result.duration_minutes,
        "latency_ms": latency_ms,
    })

    return distance_result
