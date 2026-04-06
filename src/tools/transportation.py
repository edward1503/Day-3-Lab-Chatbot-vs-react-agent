from typing import List, Dict, Any, Optional
from fast_flights import FlightData, Passengers, get_flights
from src.schemas.models import FlightInfo, FlightSearchResult


# Try to import FlightRadar24, but make it optional
try:
    from FlightRadar24 import FlightRadar24API
    FLIGHTRADAR24_AVAILABLE = True
except ImportError:
    FLIGHTRADAR24_AVAILABLE = False
    FlightRadar24API = None

def search_flight_prices(origin: str, destination: str, date: str) -> FlightSearchResult:
    """
    Tìm kiếm giá vé máy bay thực tế từ Google Flights.
    Args:
        origin: Mã IATA hoặc tên thành phố (HAN, SGN, Da Nang, ...)
        destination: Mã IATA hoặc tên thành phố
        date: Ngày bay (YYYY-MM-DD)
    """
    # Mapping đơn giản cho các thành phố phổ biến nếu không phải IATA
    iata_map = {
        "hà nội": "HAN", "hanoi": "HAN", "hn": "HAN",
        "hồ chí minh": "SGN", "saigon": "SGN", "tphcm": "SGN", "ho chi minh": "SGN", "sg": "SGN",
        "đà nẵng": "DAD", "da nang": "DAD",
        "nha trang": "CXR", "phú quốc": "PQC", "phu quoc": "PQC",
        "đà lạt": "DLI", "da lat": "DLI", "huế": "HUI", "hue": "HUI"
    }

    
    origin_iata = iata_map.get(origin.lower(), origin).upper()
    dest_iata = iata_map.get(destination.lower(), destination).upper()

    try:
        flight_data = [FlightData(date=date, from_airport=origin_iata, to_airport=dest_iata)]
        passengers = Passengers(adults=1)
        
        result = get_flights(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy"
        )
        
        flights = []
        for f in result.flights[:5]:
            flights.append(FlightInfo(
                airline=f.name,
                flight_number=None, # fast-flights doesn't specify number easily
                departure_time=f.departure,
                arrival_time=f.arrival,
                price=float(str(f.price).replace(',', '').replace('.', '').replace(' ', '').replace('VNĐ', '').replace('₫', '').strip() or 0),
                origin=origin_iata,

                destination=dest_iata
            ))
            
        best = flights[0] if flights else None
        return FlightSearchResult(flights=flights, best_option=best)
        
    except Exception as e:
        return FlightSearchResult(flights=[])


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
