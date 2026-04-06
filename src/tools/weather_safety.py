import requests
import urllib3
from typing import Dict, Any, Optional

# Tắt cảnh báo InsecureRequestWarning khi dùng verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Bảng mã thời tiết Open-Meteo
# https://open-meteo.com/en/docs
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
    71: "Tuyết rơi nhẹ (Slight snow fall)",
    73: "Tuyết rơi vừa (Moderate snow fall)",
    75: "Tuyết rơi nặng (Heavy snow fall)",
    80: "Mưa rào nhẹ (Slight rain showers)",
    81: "Mưa rào vừa (Moderate rain showers)",
    82: "Mưa rào mạnh (Violent rain showers)",
    95: "Dông nhẹ (Thunderstorm slight)",
    96: "Dông có mưa đá (Thunderstorm with hail)"
}

def get_coordinates(location: str) -> Optional[Dict[str, float]]:
    """
    Sử dụng Open-Meteo Geocoding API để đổi tên thành phố thành tọa độ (lat, lon).
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    try:
        # Thêm verify=False để tránh lỗi SSL trong một số môi trường
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return {
                "lat": result["latitude"],
                "lon": result["longitude"],
                "name": result.get("name", location),
                "country": result.get("country", "")
            }
    except Exception as e:
        print(f"Lỗi Geocoding cho {location}: {e}")
    return None

def get_weather_forecast(location: str) -> str:
    """
    [TOOL] Lấy thông tin thời tiết hiện tại cho một địa điểm cụ thể.
    """
    coords = get_coordinates(location)
    if not coords:
        return f"Không tìm thấy tọa độ cho địa điểm: {location}. Vui lòng kiểm tra lại tên thành phố."

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current_weather": "true",
        "timezone": "auto"
    }

    try:
        # Thêm verify=False để tránh lỗi SSL
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "current_weather" in data:
            cw = data["current_weather"]
            temp = cw["temperature"]
            windspeed = cw["windspeed"]
            weather_code = cw["weathercode"]
            
            # Sử dụng bảng mã WMO_CODES để mô tả chi tiết hơn
            weather_desc = WMO_CODES.get(weather_code, "Không xác định")
            
            return (f"Thời tiết hiện tại tại {coords['name']}, {coords['country']}:\n"
                    f"- Nhiệt độ: {temp}°C\n"
                    f"- Tình trạng: {weather_desc}\n"
                    f"- Tốc độ gió: {windspeed} km/h")
        
    except Exception as e:
        return f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}"

    return f"Không có dữ liệu thời tiết cho {location}."

if __name__ == "__main__":
    # Test nhanh (Hanoi / Saigon)
    print(get_weather_forecast("Hanoi"))
