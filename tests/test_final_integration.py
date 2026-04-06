
import os
import json
import asyncio
from dotenv import load_dotenv
from src.agent.travel_graph import compile_travel_graph, create_initial_state

load_dotenv()

async def run_final_test():
    print("🚀 ĐANG CHẠY BẢN TEST TOÀN DIỆN (FULL INTEGRATION TEST)...")
    print("="*60)
    
    app = compile_travel_graph()
    
    # CASE 1: Kiểm tra chặn OOD (Out-of-Domain)
    print("\n[TEST 1] Kiểm tra chặn câu hỏi ngoài phạm vi (OOD)...")
    state_ood = create_initial_state("Tôi bị đau đầu quá, nên uống thuốc gì?")
    async for output in app.astream(state_ood):
        for node_name, node_state in output.items():
            if "messages" in node_state:
                print(f"Agent (Node: {node_name}): {node_state['messages'][-1][1]}")
    
    print("-" * 30)
    
    # CASE 2: Kiểm tra luồng lập kế hoạch đầy đủ (Flights + Weather + AQI + Budget)
    print("\n[TEST 2] Kiểm tra luồng lập kế hoạch du lịch đầy đủ...")
    user_input = "Tôi muốn đi Hà Nội 3 ngày, ngân sách 10 triệu, đi từ SGN."
    print(f"User: {user_input}")
    
    state_full = create_initial_state(user_input)
    
    final_state = None
    async for output in app.astream(state_full):
        for node_name, node_state in output.items():
            print(f"▶️ Đang chạy Node: {node_name}...")
            # Lưu lại state cuối cùng để kiểm tra dữ liệu
            final_state = node_state 
            
            if node_name == "check_weather" and "weather" in node_state:
                w = node_state["weather"]
                print(f"   🌤️ Weather: {w.condition}, Temp: {w.temperature_celsius}°C")
                print(f"   🌫️ AQI: {w.aqi} ({w.aqi_description})")
                
            if node_name == "search_flights" and "flight_info" in node_state:
                f = node_state["flight_info"]
                if f:
                    print(f"   ✈️ Flight: {f.airline} - {f.price:,.0f} VNĐ")
                else:
                    print("   ✈️ Flight: Không tìm thấy vé (có thể do API hoặc IATA)")

            if node_name == "generate_plan" and "final_plan" in node_state:
                plan = node_state["final_plan"]
                print("\n✅ KẾ HOẠCH CUỐI CÙNG ĐÃ ĐƯỢC TẠO!")
                print(f"📍 Điểm đến: {plan.destination}")
                print(f"💰 Tổng chi phí dự kiến: {plan.budget.grand_total:,.0f} VNĐ")
                print(f"📝 Tóm tắt: {plan.summary[:200]}...")

    print("="*60)
    print("✅ HOÀN TẤT KIỂM THỬ TOÀN BỘ HỆ THỐNG!")

if __name__ == "__main__":
    asyncio.run(run_final_test())
