import os
import sys
import unittest
from dotenv import load_dotenv

# Thêm thư mục gốc vào sys.path để import được src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.weather_safety import get_coordinates, get_weather_forecast
from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider

class TestWeatherTool(unittest.TestCase):
    
    def test_get_coordinates_success(self):
        """Kiểm tra lấy tọa độ thành công cho Hà Nội."""
        coords = get_coordinates("Hanoi")
        self.assertIsNotNone(coords)
        self.assertIn("lat", coords)
        self.assertIn("lon", coords)
        self.assertEqual(coords["name"], "Hanoi")

    def test_get_coordinates_failure(self):
        """Kiểm tra xử lý khi địa điểm không tồn tại."""
        coords = get_coordinates("NonExistentCity12345")
        self.assertIsNone(coords)

    def test_get_weather_forecast_hanoi(self):
        """Kiểm tra lấy thời tiết Hà Nội trả về chuỗi hợp lệ."""
        result = get_weather_forecast("Hanoi")
        self.assertIn("Thời tiết hiện tại tại Hanoi", result)
        self.assertIn("Nhiệt độ", result)

    def test_agent_integration_mock(self):
        """
        Kiểm tra tích hợp: Agent có thể gọi tool weather.
        (Sử dụng mock hoặc chạy thật nếu có API Key)
        """
        load_dotenv()
        # Chú ý: Test này cần OPENAI_API_KEY nếu chạy thực tế. 
        # Ở đây chúng ta chỉ test logic gọi tool trong agent._execute_tool
        provider = OpenAIProvider()
        tools = [{"name": "get_weather_forecast", "description": "Lấy thời tiết"}]
        agent = ReActAgent(llm=provider, tools=tools)
        
        # Test trực tiếp hàm _execute_tool của Agent
        response = agent._execute_tool("get_weather_forecast", {"location": "Hanoi"})
        self.assertIn("Hanoi", response)
        self.assertIn("Nhiệt độ", response)

if __name__ == "__main__":
    print("--- Running Weather Tool Tests ---")
    unittest.main()
