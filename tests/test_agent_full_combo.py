import os
import sys
from dotenv import load_dotenv

# Thêm src vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider

def test_agent_safety_combo():
    """
    Demo Agent kết hợp: Weather + Air Quality + Flights.
    """
    load_dotenv()
    provider = OpenAIProvider()
    
    # Danh sách công cụ đầy đủ
    tools = [
        {
            "name": "get_weather_forecast",
            "description": "Lấy thông tin thời tiết hiện tại của một địa điểm.",
            "parameters": "{'location': 'Tên thành phố (Vd: Hà Nội, Dalat)'}"
        },
        {
            "name": "get_air_quality",
            "description": "Kiểm tra chỉ số chất lượng không khí (AQI) và mức độ ô nhiễm.",
            "parameters": "{'location': 'Tên thành phố (Vd: Hà Nội, Saigon)'}"
        },
        {
            "name": "search_flight_prices",
            "description": "Tìm kiếm giá vé máy bay thực tế từ Google Flights cho ngày cụ thể.",
            "parameters": "{'origin': 'Mã IATA sân bay đi', 'destination': 'Mã IATA sân bay đến', 'date': 'Ngày định dạng YYYY-MM-DD'}"
        }
    ]
    
    agent = ReActAgent(llm=provider, tools=tools)
    
    # Kịch bản: Kiểm tra ô nhiễm và thời tiết trước khi đi
    user_input = "Mình nghe nói dạo này Sài Gòn đang bị ô nhiễm không khí nặng lắm, bạn check giúp mình chất lượng không khí và thời tiết ở đó hiện tại thế nào với?"
    
    print(f"\n--- Scenario: Environmental Safety Check (Weather + AQI) ---")
    print(f"User: {user_input}")
    response = agent.run(user_input)
    print(f"Agent Final Answer:\n{response}")

if __name__ == "__main__":
    test_agent_safety_combo()
