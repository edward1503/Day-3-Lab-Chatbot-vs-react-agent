from typing import List, Dict, Any, Optional
from fast_flights import FlightData, Passengers, get_flights

# Try to import FlightRadar24, but make it optional
try:
    from FlightRadar24 import FlightRadar24API
    FLIGHTRADAR24_AVAILABLE = True
except ImportError:
    FLIGHTRADAR24_AVAILABLE = False
    FlightRadar24API = None

def search_flight_prices(origin: str, destination: str, date: str) -> str:
    """
    [Member B] Tìm kiếm giá vé máy bay thực tế từ Google Flights cho ngày cụ thể.
    Args:
        origin: Mã IATA sân bay đi (VD: HAN, SGN)
        destination: Mã IATA sân bay đến
        date: Ngày bay (YYYY-MM-DD)
    """
    try:
        # GPT-4o sẽ tự động cung cấp mã IATA nên chúng ta dùng trực tiếp
        flight_data = [FlightData(date=date, from_airport=origin.upper(), to_airport=destination.upper())]
        passengers = Passengers(adults=1)
        
        result = get_flights(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy"
        )
        
        if not result.flights:
            return f"Không tìm thấy vé máy bay từ {origin} đến {destination} vào ngày {date}."

        output = f"✈️ KẾT QUẢ GIÁ VÉ ({origin.upper()} -> {destination.upper()}, ngày {date}):\n"
        for i, flight in enumerate(result.flights[:5]):
            output += f"{i+1}. {flight.name}: {flight.price} (Khởi hành: {flight.departure}, Đến: {flight.arrival})\n"
        
        return output
    except Exception as e:
        return f"Lỗi khi tìm kiếm giá vé: {str(e)}"

def track_flight_status(flight_number: str) -> str:
    """
    [Member B] Theo dõi trạng thái hành trình thực tế của một chuyến bay đang hoạt động (Real-time).
    Args:
        flight_number: Số hiệu chuyến bay (VD: VN213, VJ123)
    """
    if not FLIGHTRADAR24_AVAILABLE:
        return (f"⚠️  FlightRadar24 module không có sẵn. "
                f"Chuyên bay {flight_number} có thể được theo dõi tại https://www.flightradar24.com/")
    
    try:
        api = FlightRadar24API()
        airline_prefix = flight_number[:2].upper()
        airline_map = {"VN": "HVN", "VJ": "VJC", "QH": "BAV", "VU": "VAG"}
        icao_code = airline_map.get(airline_prefix, airline_prefix)
        
        flights = api.get_flights(airline=icao_code)
        target_flight = None
        for f in flights:
            if flight_number.upper() in f.number.upper() or flight_number.upper() in f.registration.upper():
                target_flight = f
                break
        
        if not target_flight:
            return f"Hiện tại không tìm thấy chuyến bay {flight_number} đang hoạt động trên radar."

        status = f"📍 TRẠNG THÁI CHUYẾN BAY {flight_number}:\n"
        status += f"- Tuyến: {target_flight.origin_airport_iata} -> {target_flight.destination_airport_iata}\n"
        status += f"- Độ cao: {target_flight.altitude} ft\n"
        status += f"- Tốc độ: {target_flight.ground_speed} kt\n"
        status += f"- Máy bay: {target_flight.aircraft_code}\n"
        status += f"- Link theo dõi: https://www.flightradar24.com/{target_flight.callsign}\n"
        
        return status
    except Exception as e:
        return f"Lỗi khi theo dõi chuyến bay: {str(e)}"
