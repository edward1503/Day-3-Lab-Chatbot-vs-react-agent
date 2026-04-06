import requests
from typing import Dict, Any, Optional

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
        response = requests.get(url, params=params)
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
        print(f"Lỗi Geocoding: {e}")
    return None

def get_weather_forecast(location: str) -> str:
    """
    [TOOL] Lấy thông tin thời tiết hiện tại cho một địa điểm cụ thể.
    """
    coords = get_coordinates(location)
    if not coords:
        return f"Không tìm thấy tọa độ cho địa điểm: {location}"

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current_weather": "true",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "current_weather" in data:
            cw = data["current_weather"]
            temp = cw["temperature"]
            windspeed = cw["windspeed"]
            # Open-Meteo weather codes: https://open-meteo.com/en/docs
            weather_code = cw["weathercode"]
            
            # Đơn giản hóa weather code (có thể mapping kỹ hơn nếu cần)
            weather_desc = "Trong lành/Mây nhẹ" if weather_code <= 3 else "Có mây/Mưa/Bão"
            
            return (f"Thời tiết hiện tại tại {coords['name']}, {coords['country']}:\n"
                    f"- Nhiệt độ: {temp}°C\n"
                    f"- Tình trạng: {weather_desc}\n"
                    f"- Tốc độ gió: {windspeed} km/h")
        
    except Exception as e:
        return f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}"

    return f"Không có dữ liệu thời tiết cho {location}."

if __name__ == "__main__":
    # Test nhanh
    print(get_weather_forecast("Hanoi"))
