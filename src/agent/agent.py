import os
import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class AgentAction(BaseModel):
    thought: str = Field(description="Suy luận của Agent về bước tiếp theo")
    action: Optional[str] = Field(None, description="Tên công cụ cần gọi (ví dụ: get_weather_forecast)")
    action_input: Optional[Dict[str, Any]] = Field(None, description="Tham số truyền vào cho công cụ")
    final_answer: Optional[str] = Field(None, description="Câu trả lời cuối cùng cho người dùng")

class ReActAgent:
    """
    Hệ thống Agent ReAct cho Trợ Lý Lên Kế Hoạch Du Lịch.
    Sử dụng Thought-Action-Observation loop và Pydantic để parse kết quả.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']} (Params: {t.get('parameters', 'None')})" for t in self.tools])
        return f"""
        Bạn là một Trợ Lý Lên Kế Hoạch Du Lịch Thông Minh. Bạn có quyền truy cập vào các công cụ sau:
        {tool_descriptions}

        QUY TẮC QUAN TRỌNG:
        1. LUÔN LUÔN trả về kết quả dưới định dạng JSON khớp với schema sau:
        {{
            "thought": "suy luận của bạn",
            "action": "tên_công_cụ_hoặc_null",
            "action_input": {{ "param_name": "value" }} hoặc null,
            "final_answer": "câu_trả_lời_cuối_cùng_hoặc_null"
        }}
        2. Nếu bạn đã có câu trả lời cuối cùng hoặc công cụ (Tool) trả về kết quả "Không tìm thấy/Lỗi", hãy giải thích cho người dùng trong 'final_answer' và kết thúc (để 'action' là null).
        3. Tuyệt đối KHÔNG gọi lại cùng một công cụ với cùng tham số nếu nó đã trả về kết quả không tìm thấy ở bước trước đó.
        4. Hãy tận dụng kiến thức của bạn để tự động chuyển đổi tên địa danh (Vd: Hà Nội, Sài Gòn) sang mã sân bay IATA (Vd: HAN, SGN) khi gọi các công cụ tìm kiếm máy bay.
        5. Luôn giữ phong cách phản hồi thân thiện, chuyên nghiệp.
        6. KHÔNG ĐƯỢC trả về bất kỳ văn bản nào nằm ngoài định dạng JSON này.
        """

    def run(self, user_input: str, skip_ood: bool = False) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # --- PHASE 0: OOD CHECK ---
        # (Đơn giản hóa bằng cách hỏi LLM trực tiếp hoặc dùng regex)
        if not skip_ood and self._is_out_of_domain(user_input):
            return "Xin lỗi, tôi là trợ lý du lịch. Tôi không thể hỗ trợ các vấn đề nằm ngoài phạm vi du lịch như y tế, chính trị hay lập trình."


        history = [{"role": "user", "content": user_input}]
        steps = 0

        while steps < self.max_steps:
            # Format history thành chuỗi liên tục để LLM không bị quên ngữ cảnh
            full_prompt = ""
            for msg in history:
                full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
                
            # 1. Gọi LLM để lấy Thought/Action
            response = self.llm.generate(
                prompt=full_prompt.strip(), 
                system_prompt=self.get_system_prompt()
            )

            
            # Ghi log metrics cho từng bước gọi LLM
            tracker.track_request(
                provider=response["provider"],
                model=self.llm.model_name,
                usage=response["usage"],
                latency_ms=response["latency_ms"]
            )

            llm_output = response["content"]
            
            try:
                # 2. Parse JSON output dùng Pydantic
                # Làm sạch chuỗi trước khi parse (loại bỏ markdown code blocks nếu có)
                clean_json = re.sub(r'```json\s*|\s*```', '', llm_output).strip()
                action_data = AgentAction.model_validate_json(clean_json)
                
                logger.log_event("AGENT_STEP", action_data.model_dump())

                # 3. Kiểm tra Final Answer
                if action_data.final_answer:
                    logger.log_event("AGENT_END", {"status": "success", "steps": steps + 1})
                    return action_data.final_answer

                # 4. Thực thi Action
                if action_data.action:
                    # Ghi nhớ lại thought+action của model
                    history.append({
                        "role": "assistant",
                        "content": clean_json
                    })
                    
                    observation = self._execute_tool(action_data.action, action_data.action_input or {})
                    history.append({
                        "role": "system", 
                        "content": f"Observation: {observation}"
                    })

                else:
                    break

            except (ValidationError, json.JSONDecodeError) as e:
                logger.error(f"Lỗi parse JSON hoặc Validate: {e}")
                history.append({
                    "role": "assistant",
                    "content": llm_output
                })
                history.append({
                    "role": "system", 
                    "content": f"Lỗi định dạng JSON: Vui lòng thử lại và chỉ trả về JSON hợp lệ."
                })


            steps += 1
            
        logger.log_event("AGENT_END", {"status": "timeout", "steps": steps})
        return "Tôi đã cố gắng xử lý nhưng không tìm ra câu trả lời cuối cùng trong giới hạn bước cho phép."

    def _is_out_of_domain(self, user_input: str) -> bool:
        """
        Sử dụng LLM để phân loại liệu câu hỏi của người dùng có nằm trong phạm vi hỗ trợ (Du lịch & Thời tiết) hay không.
        """
        classification_prompt = f"""
        Bạn là một chuyên gia phân loại ý định (Intent Classifier). 
        Nhiệm vụ của bạn là xác định xem câu hỏi của người dùng có liên quan đến các chủ đề sau hay không:
        1. Du lịch (Travel): Tìm vé máy bay, khách sạn, địa điểm tham quan, lịch trình.
        2. Thời tiết (Weather): Dự báo thời tiết, chất lượng không khí tại một địa điểm.
        3. Các lời chào hỏi xã giao thông thường.

        Nếu câu hỏi LIÊN QUAN đến các chủ đề trên, hãy trả về: IN_DOMAIN
        Nếu câu hỏi KHÔNG LIÊN QUAN (Ví dụ: Y tế, Chính trị, Lập trình, Nấu ăn, hack, hoặc các chủ đề khác), hãy trả về: OOD

        User input: "{user_input}"
        
        Trả về DUY NHẤT từ 'IN_DOMAIN' hoặc 'OOD'.
        """
        
        try:
            response = self.llm.generate(
                prompt=classification_prompt,
                system_prompt="Bạn là một trợ lý phân loại ý định chính xác."
            )
            result = response["content"].strip().upper()
            
            # Đôi khi LLM có thể trả về thêm text, ta check xem có chứa OOD không
            if "OOD" in result and "IN_DOMAIN" not in result:
                logger.log_event("OOD_DETECTED", {"input": user_input, "reason": "LLM_CLASSIFIER"})
                return True
            if "IN_DOMAIN" in result:
                return False
                
            # Fallback về keyword nếu LLM không trả về đúng định dạng
            off_topic_keywords = ["thuốc", "bệnh", "code", "lập trình", "chính trị", "đảng", "hack"]
            for kw in off_topic_keywords:
                if kw in user_input.lower():
                    return True
        except Exception as e:
            logger.error(f"Lỗi khi gọi LLM cho OOD check: {e}")
            
        return False

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        # Import động các công cụ đã được Member A, B, C, D định nghĩa
        try:
            if tool_name == "get_weather_forecast":
                from src.tools.weather_tool import get_weather_forecast

                return get_weather_forecast(**args)
            elif tool_name == "get_air_quality":
                # AQI is also now in weather_tool
                from src.tools.weather_tool import get_weather_forecast as get_air_quality

                return get_air_quality(**args)
            elif tool_name == "search_flight_prices":
                from src.tools.transportation import search_flight_prices
                return str(search_flight_prices(**args))
            elif tool_name == "track_flight_status":
                from src.tools.transportation import track_flight_status
                return str(track_flight_status(**args))
            elif tool_name == "search_hotels":
                from src.tools.stays_hotels import search_hotels
                return str(search_hotels(**args))
            elif tool_name == "explore_top_attractions":
                from src.tools.activities_itinerary import explore_top_attractions
                return str(explore_top_attractions(**args))
            elif tool_name == "search_by_category":
                from src.tools.activities_itinerary import search_by_category
                return str(search_by_category(**args))
            elif tool_name == "get_itinerary_suggestion":
                from src.tools.activities_itinerary import get_itinerary_suggestion
                return str(get_itinerary_suggestion(**args))
            elif tool_name == "get_hotel_details":
                from src.tools.stays_hotels import get_hotel_details
                return str(get_hotel_details(**args))
            elif tool_name == "compare_hotels":
                from src.tools.stays_hotels import compare_hotels
                return str(compare_hotels(**args))
            # ... Thêm các tool khác tại đây
        except Exception as e:
            return f"Cần cung cấp dữ liệu hợp lệ cho {tool_name}. Lỗi: {str(e)}"
            
        return f"Công cụ {tool_name} chưa được tích hợp hoàn toàn."
