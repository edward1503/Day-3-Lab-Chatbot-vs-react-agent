import requests
import urllib3
from typing import Dict, Any, Optional

# Tắt cảnh báo InsecureRequestWarning khi dùng verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Bảng mã thời tiết WMO
WMO_CODES = {
    0: "Trời quang đãng (Clear sky)",
    1: "Trời ít mây (Mainly clear)",
    2: "Trời nhiều mây (Partly cloudy)",
    3: "Trời u ám (Overcast)",
    45: "Sương mù (Fog)",
    48: "Sương giá rải rác (Depositing rime fog)",
    51: "Mưa phùn nhẹ (Light drizzle)",
    53: "Mưa phùn vừa (Moderate drizzle)",
    55: "Mưa phùn nặng (Dense drizzle)",
    61: "Mưa nhẹ (Slight rain)",
    63: "Mưa vừa (Moderate rain)",
    65: "Mưa to (Heavy rain)",
    80: "Mưa rào nhẹ (Slight rain showers)",
    81: "Mưa rào vừa (Moderate rain showers)",
    82: "Mưa rào mạnh (Violent rain showers)",
    95: "Dông nhẹ (Thunderstorm slight)",
    96: "Dông có mưa đá (Thunderstorm with hail)"
}

def get_coordinates(location: str) -> Optional[Dict[str, float]]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location, "count": 1, "language": "en", "format": "json"}
    try:
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return {"lat": result["latitude"], "lon": result["longitude"], "name": result.get("name", location), "country": result.get("country", "")}
    except Exception as e:
        print(f"Lỗi Geocoding cho {location}: {e}")
    return None

def get_weather_forecast(location: str) -> str:
    """
    [TOOL] Lấy thông tin thời tiết hiện tại cho một địa điểm.
    """
    coords = get_coordinates(location)
    if not coords:
        return f"Không tìm thấy tọa độ cho địa điểm: {location}."

    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": coords["lat"], "longitude": coords["lon"], "current_weather": "true", "timezone": "auto"}

    try:
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "current_weather" in data:
            cw = data["current_weather"]
            weather_desc = WMO_CODES.get(cw["weathercode"], "Không xác định")
            return (f"🌤️ THỜI TIẾT TẠI {coords['name'].upper()}, {coords['country']}:\n"
                    f"- Nhiệt độ: {cw['temperature']}°C\n"
                    f"- Tình trạng: {weather_desc}\n"
                    f"- Tốc độ gió: {cw['windspeed']} km/h")
    except Exception as e:
        return f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}"
    return f"Không có dữ liệu thời tiết cho {location}."

def get_air_quality(location: str) -> str:
    """
    [TOOL] Kiểm tra chỉ số chất lượng không khí (AQI) và mức độ ô nhiễm tại một địa điểm.
    """
    coords = get_coordinates(location)
    if not coords:
        return f"Không tìm thấy tọa độ để kiểm tra không khí tại: {location}."

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current": "european_aqi,pm10,pm2_5",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "current" in data:
            curr = data["current"]
            aqi = curr["european_aqi"]
            pm10 = curr["pm10"]
            pm25 = curr["pm2_5"]

            # Phân loại mức độ AQI (Chuẩn Châu Âu)
            if aqi <= 20: status = "Rất tốt (Great)"
            elif aqi <= 40: status = "Tốt (Good)"
            elif aqi <= 60: status = "Trung bình (Fair)"
            elif aqi <= 80: status = "Kém (Poor)"
            elif aqi <= 100: status = "Rất kém (Very Poor)"
            else: status = "Cực kỳ kém (Extremely Poor)"

            return (f"🌬️ CHẤT LƯỢNG KHÔNG KHÍ TẠI {coords['name'].upper()}:\n"
                    f"- Chỉ số AQI: {aqi} ({status})\n"
                    f"- Bụi mịn PM2.5: {pm25} µg/m³\n"
                    f"- Bụi mịn PM10: {pm10} µg/m³")
    except Exception as e:
        return f"Lỗi khi kiểm tra chất lượng không khí: {str(e)}"
    return f"Không có dữ liệu không khí cho {location}."

if __name__ == "__main__":
    # Test nhanh
    print(get_air_quality("Hanoi"))
