"""
Tool: get_weather_forecast
Kiểm tra thời tiết tại điểm đến bằng OpenWeatherMap API.

API Docs: https://openweathermap.org/forecast5
Endpoint: https://api.openweathermap.org/data/2.5/forecast
"""

import os
import time
from collections import Counter

import requests
from dotenv import load_dotenv

from src.schemas.models import WeatherInfo
from src.telemetry.logger import logger

load_dotenv()

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Weather codes mà chỉ ra mưa/bão
RAINY_MAIN_CONDITIONS = {"Rain", "Drizzle", "Thunderstorm"}


def get_weather_forecast(city: str, days: int = 3) -> WeatherInfo:
    """
    Lấy dự báo thời tiết cho thành phố trong N ngày tới.

    Args:
        city: Tên thành phố (ví dụ: "Da Nang", "Hanoi", "Ho Chi Minh City")
        days: Số ngày cần dự báo (1-5, API free hỗ trợ tối đa 5 ngày)

    Returns:
        WeatherInfo: Thông tin thời tiết đã parse
    """
    start_time = time.time()
    logger.log_event("TOOL_START", {"tool": "get_weather_forecast", "city": city, "days": days})

    if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "your_openweathermap_key_here":
        raise ValueError("Chưa cấu hình OPENWEATHERMAP_API_KEY trong file .env")

    # Gọi API OpenWeatherMap
    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric",
        "lang": "vi",
        "cnt": min(days * 8, 40),  # Mỗi ngày 8 data points (3h interval), max 5 ngày
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Parse dữ liệu từ response
    forecasts = data.get("list", [])
    if not forecasts:
        raise ValueError(f"Không có dữ liệu dự báo cho thành phố '{city}'")

    temps = [f["main"]["temp"] for f in forecasts]
    humidities = [f["main"]["humidity"] for f in forecasts]
    conditions = [f["weather"][0]["main"] for f in forecasts]
    descriptions = [f["weather"][0].get("description", "") for f in forecasts]
    wind_speeds = [f.get("wind", {}).get("speed", 0) for f in forecasts]

    # Tính trung bình
    avg_temp = sum(temps) / len(temps)
    avg_humidity = int(sum(humidities) / len(humidities))
    avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else None

    # Xác định condition chính (most frequent)
    main_condition = Counter(conditions).most_common(1)[0][0]

    # Xác định is_rainy
    is_rainy = any(c in RAINY_MAIN_CONDITIONS for c in conditions)

    # Lấy icon từ entry đầu tiên
    icon = forecasts[0]["weather"][0].get("icon")

    # Tạo forecast summary bằng tiếng Việt
    rainy_count = sum(1 for c in conditions if c in RAINY_MAIN_CONDITIONS)
    total_entries = len(conditions)
    rain_percent = int(rainy_count / total_entries * 100)

    condition_vi_map = {
        "Clear": "Trời quang",
        "Clouds": "Nhiều mây",
        "Rain": "Có mưa",
        "Drizzle": "Mưa phùn",
        "Thunderstorm": "Dông bão",
        "Snow": "Có tuyết",
        "Mist": "Sương mù",
        "Fog": "Sương mù dày",
        "Haze": "Mù khô",
    }
    condition_vi = condition_vi_map.get(main_condition, main_condition)

    forecast_summary = (
        f"Dự báo {days} ngày tới tại {city}: {condition_vi}, "
        f"nhiệt độ trung bình {avg_temp:.1f}°C, "
        f"độ ẩm {avg_humidity}%. "
    )
    if is_rainy:
        forecast_summary += f"Xác suất mưa khoảng {rain_percent}% thời gian. Nên chuẩn bị áo mưa."
    else:
        forecast_summary += "Thời tiết thuận lợi cho các hoạt động ngoài trời."

    latency_ms = int((time.time() - start_time) * 1000)

    result = WeatherInfo(
        city=data.get("city", {}).get("name", city),
        temperature_celsius=round(avg_temp, 1),
        condition=main_condition,
        humidity=avg_humidity,
        is_rainy=is_rainy,
        forecast_summary=forecast_summary,
        wind_speed=round(avg_wind, 1) if avg_wind else None,
        icon=icon,
    )

    logger.log_event("TOOL_COMPLETE", {
        "tool": "get_weather_forecast",
        "city": city,
        "condition": main_condition,
        "is_rainy": is_rainy,
        "temp": round(avg_temp, 1),
        "latency_ms": latency_ms,
    })

    return result
