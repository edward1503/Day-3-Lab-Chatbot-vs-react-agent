from fast_flights import FlightData, Passengers, get_flights
from datetime import datetime, timedelta

def test_vietnam_flights():
    # Chọn ngày sau 2 tuần: HAN -> SGN
    test_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    print(f"--- Testing Fast-Flights (HAN -> SGN) on {test_date} ---")
    
    # API v2.2 uses FlightData and get_flights directly
    flight_data = [
        FlightData(
            date=test_date,
            from_airport="HAN",
            to_airport="SGN",
        )
    ]
    passengers = Passengers(adults=1)
    
    try:
        # get_flights return a Result object
        result = get_flights(
            flight_data=flight_data,
            trip="one-way",
            passengers=passengers,
            seat="economy"
        )
        
        if not result.flights:
            print("No flights found. Check if the date/route is valid.")
            return

        print(f"Found {len(result.flights)} flights.\n")
        
        # In ra 10 chuyến bay đầu tiên
        for i, flight in enumerate(result.flights[:10]):
            print(f"{i+1}. {flight.name}: {flight.price} - Dep: {flight.departure} -> Arr: {flight.arrival}")
            
        # Kiểm tra hãng
        airlines = [f.name.lower() for f in result.flights]
        has_vj = any("vietjet" in a for a in airlines)
        has_bb = any("bamboo" in a for a in airlines)
        
        print(f"\nVietjet Air found: {has_vj}")
        print(f"Bamboo Airways found: {has_bb}")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_vietnam_flights()
