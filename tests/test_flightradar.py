from FlightRadar24 import FlightRadar24API
import json

def test_flightradar():
    api = FlightRadar24API()
    
    print("--- Searching for Vietnam Airlines (HVN) Flights ---")
    hvn_flights = api.get_flights(airline="HVN")
    print(f"Found {len(hvn_flights)} HVN flights currently in the air.")
    
    if hvn_flights:
        sample = hvn_flights[0]
        # details = api.get_flight_details(sample) # This usually requires more data
        print(f"\nSample Flight Info:")
        print(f"Flight ID: {sample.id}")
        print(f"Callsign: {sample.callsign}")
        print(f"Number: {sample.number}")
        print(f"Origin: {sample.origin_airport_iata}")
        print(f"Destination: {sample.destination_airport_iata}")
        print(f"Altitude: {sample.altitude} ft")
        print(f"Ground Speed: {sample.ground_speed} kt")

    print("\n--- Searching for VietJet Air (VJC) Flights ---")
    vjc_flights = api.get_flights(airline="VJC")
    print(f"Found {len(vjc_flights)} VJC flights currently in the air.")
    
    print("\n--- Searching for Bamboo Airways (BAV) Flights ---")
    bav_flights = api.get_flights(airline="BAV")
    print(f"Found {len(bav_flights)} BAV flights currently in the air.")

if __name__ == "__main__":
    test_flightradar()
