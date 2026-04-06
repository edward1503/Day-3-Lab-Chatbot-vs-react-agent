import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider

def run_chatbot():
    """
    [BASELINE] Chatbot cơ bản sử dụng duy nhất Prompt, không có Tool Calling.
    Phục vụ cho việc so sánh hiệu năng (Metrics) trong Lab 3.
    """
    load_dotenv()
    
    # Khởi tạo Provider (mặc định lấy từ .env)
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai")
    model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")
    
    if provider_name == "openai":
        provider = OpenAIProvider(model_name=model_name)
    elif provider_name == "google":
        provider = GeminiProvider(model_name=model_name)
    else:
        provider = LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH"))

    print(f"--- Chatbot Baseline ({provider_name}) ---")
    print("Nhập 'quit' để thoát.")

    while True:
        user_input = input("\nBạn: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        print("Trợ lý: ", end="", flush=True)
        for chunk in provider.stream(user_input):
            print(chunk, end="", flush=True)
        print()

if __name__ == "__main__":
    run_chatbot()
