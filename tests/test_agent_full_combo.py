import os
import sys
from dotenv import load_dotenv

# Thêm src vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider

def test_agent_full_combo():
    """
    Demo Agent kết hợp: Thời tiết (Member A) + Tìm vé (Member B).
    """
    load_dotenv()
    provider = OpenAIProvider()
    
    # Định nghĩa danh sách các công cụ ĐÃ CẬP NHẬT (A + B)
    tools = [
        {
            "name": "get_weather_forecast",
            "description": "Lấy thông tin thời tiết hiện tại của một địa điểm.",
            "parameters": "{'location': 'Tên thành phố (Vd: Hà Nội, Đà Lạt)'}"
        },
        {
            "name": "search_flight_prices",
            "description": "Tìm kiếm giá vé máy bay thực tế từ Google Flights. Model tự chuyển tên thành phố sang mã IATA.",
            "parameters": "{'origin': 'Mã IATA sân bay đi', 'destination': 'Mã IATA sân bay đến', 'date': 'Ngày định dạng YYYY-MM-DD'}"
        },
        {
            "name": "track_flight_status",
            "description": "Theo dõi trạng thái thực tế của một chuyến bay đang bay (Real-time).",
            "parameters": "{'flight_number': 'Mã hiệu chuyến bay'}"
        }
    ]
    
    agent = ReActAgent(llm=provider, tools=tools)
    
    # Kịch bản: Hỏi thời tiết trước khi tìm vé
    user_input = "Cho mình hỏi thời tiết ở Đà Lạt hiện tại thế nào? Và tiện thể tìm giúp mình vé từ Hà Nội đi Đà Lạt ngày 20/04/2026 luôn nhé."
    
    print(f"\n--- Scenario: Full Travel Combo (Weather + Flights) ---")
    print(f"User: {user_input}")
    response = agent.run(user_input)
    print(f"Agent Final Answer:\n{response}")

if __name__ == "__main__":
    test_agent_full_combo()
