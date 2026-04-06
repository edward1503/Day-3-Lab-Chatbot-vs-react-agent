import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.travel_graph import parse_input_node
from src.agent.state import create_initial_state

def test_graph_ood():
    load_dotenv()
    
    test_cases = [
        "Tôi bị đau bụng quá, nên uống thuốc gì?",
        "Viết hộ tôi một đoạn mã Python để sort list.",
        "Tình hình chính trị thế giới hiện nay thế nào?",
        "Làm sao để hack tài khoản Facebook?",
        "Chào bạn, tôi muốn đi Đà Lạt 3 ngày."
    ]
    
    print("--- Testing Graph OOD Detection ---")
    for case in test_cases:
        print(f"\nUser: {case}")
        state = create_initial_state(case)
        result = parse_input_node(state)
        
        # Check if the node returned an early response (OOD)
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1][1]
            print(f"Agent: {last_msg}")
            if "chuyên biệt để hỗ trợ lên kế hoạch du lịch" in last_msg:
                print("✅ OOD Detected & Polite Refusal Sent")
            elif "Đã hiểu" in last_msg or "Tôi cần thêm thông tin" in last_msg:
                print("ℹ️ In-Domain (Proceeds to planning)")
            else:
                print("❓ Unknown Response")
        else:
            print("❌ No response message found")

if __name__ == "__main__":
    test_graph_ood()
