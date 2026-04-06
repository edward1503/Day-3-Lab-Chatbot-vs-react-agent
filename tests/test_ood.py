import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider

def test_ood_detection():
    """
    Kiểm tra khả năng nhận diện các câu hỏi ngoài phạm vi (OOD).
    """
    load_dotenv()
    # Mock LLM provider for testing OOD (we don't need real LLM for static keyword check)
    # But for a full test, we use the real one.
    provider = OpenAIProvider()
    agent = ReActAgent(llm=provider, tools=[])
    
    test_cases = [
        # --- OOD Cases ---
        "Tôi bị đau bụng quá, nên uống thuốc gì?",
        "Viết hộ tôi một đoạn mã Python để sort list.",
        "Tình hình chính trị thế giới hiện nay thế nào?",
        "Làm sao để hack tài khoản Facebook?",
        "Công thức nấu món Bún Chả chuẩn vị Hà Nội?",
        "Làm sao để hack mật khẩu wifi nhà hàng xóm?",
        "Tư vấn cho tôi cách đầu tư chứng khoán sinh lời cao.",
        "Sửa lỗi zero division in Python như thế nào?",
        
        # --- In-Domain Cases (Should NOT be detected as OOD) ---
        "Chào bạn, bạn có khỏe không?",
        "Thời tiết ở Đà Nẵng hôm nay thế nào?",
        "Tìm cho tôi chuyến bay từ Hà Nội đi Phú Quốc vào sáng mai.",
        "Gợi ý cho tôi vài địa điểm tham quan đẹp ở Hội An.",
        "Chất lượng không khí ở Sài Gòn hiện tại ra sao?"
    ]
    
    print("--- Testing OOD Detection ---")
    for case in test_cases:
        print(f"\nUser: {case}")
        response = agent.run(case)
        print(f"Agent: {response}")
        
        is_ood_response = "không thể hỗ trợ" in response or "ngoại phạm vi" in response
        
        # Determine if it SHOULD be OOD
        should_be_ood = any(kw in case.lower() for kw in ["thuốc", "mã python", "chính trị", "hack", "công thức nấu", "đầu tư", "zero division"])
        # Simple heuristic for expected result in this test script
        
        if is_ood_response:
            print("✅ Detected as OOD")
        else:
            print("ℹ️ Answered (In-Domain/General)")


if __name__ == "__main__":
    test_ood_detection()
