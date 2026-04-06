import os
import time
from typing import Dict, Any, Optional, Generator
from google import genai
from src.core.llm_provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        # In Gemini, system instruction can be passed manually if needed
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0)
            }

        return {
            "content": response.text,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        responseStream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=full_prompt
        )
        for chunk in responseStream:
            yield chunk.text

    def chat_with_tools(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[list] = None) -> str:
        """
        Gọi LLM để tự động sử dụng function calling (tools) nếu cần thiết, 
        và trả về string tổng hợp mượt mà.
        """
        from google.genai import types
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        # Cấu hình chat, gắn mảng các python native functions vào
        config = types.GenerateContentConfig(
            tools=tools if tools else []
        )
        
        # Bắt đầu chat để hỗ trợ automatic function calling
        # Trong SDK mới, dùng client.chats.create để LLM tự gọi Tool và tự fetch loop
        chat = self.client.chats.create(model=self.model_name, config=config)
        response = chat.send_message(full_prompt)
        
        return response.text
