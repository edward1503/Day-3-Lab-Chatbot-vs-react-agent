import os
import sys
from dotenv import load_dotenv

# Thêm src vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider

def test_agent_expanded_transport():
    """
    Kiểm tra Agent với bộ công cụ Transportation mở rộng (Giá vé + Theo dõi).
    Dựa trên sự thông minh của GPT-4o để chuyển đổi địa danh sang mã IATA.
    """
    load_dotenv()
    provider = OpenAIProvider()
    
    # Định nghĩa danh sách các công cụ ĐÃ CẬP NHẬT cho Agent
    tools = [
        {
            "name": "search_flight_prices",
            "description": "Tìm kiếm giá vé máy bay thực tế từ Google Flights cho ngày cụ thể. Model phải tự chuyển tên thành phố sang mã IATA 3 chữ cái.",
            "parameters": "{'origin': 'Mã IATA sân bay đi (VD: HAN, SGN)', 'destination': 'Mã IATA sân bay đến', 'date': 'Ngày định dạng YYYY-MM-DD'}"
        },
        {
            "name": "track_flight_status",
            "description": "Theo dõi vị trí và trạng thái thực tế của một chuyến bay đang bay dựa trên mã số (VD: VN213, VJ123).",
            "parameters": "{'flight_number': 'Mã hiệu chuyến bay'}"
        }
    ]
    
    agent = ReActAgent(llm=provider, tools=tools)
    
    # Kịch bản 1: Tìm giá vé (Dựa vào GPT-4o để dịch 'Hà Nội' -> 'HAN')
    user_input_1 = "Tìm giúp mình vé máy bay từ Hà Nội đi Sài Gòn ngày 20/04/2026."
    print(f"\n--- Scenario 1: Searching Flight Prices (LLM handles IATA) ---")
    print(f"User: {user_input_1}")
    response_1 = agent.run(user_input_1)
    print(f"Agent Answer: {response_1}")

    # Kịch bản 2: Theo dõi hành trình
    user_input_2 = "Mình muốn biết chuyến bay VN772 hiện giờ đang ở đâu rồi?"
    print(f"\n--- Scenario 2: Real-time Tracking ---")
    print(f"User: {user_input_2}")
    response_2 = agent.run(user_input_2)
    print(f"Agent Answer: {response_2}")

if __name__ == "__main__":
    test_agent_expanded_transport()
