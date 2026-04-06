"""
🧳 Travel Planner Agent — Gradio UI
Entry point: python app.py

Giao diện chat cho Travel Planning Agent.
Hỗ trợ human-in-the-loop khi cần thay đổi kế hoạch do thời tiết.
"""

import os
import gradio as gr
from dotenv import load_dotenv

from src.agent.travel_graph import (
    compile_travel_graph,
    create_initial_state,
    process_replan_response_node,
    search_attractions_node,
    calculate_distances_node,
    find_hotels_node,
    estimate_budget_node,
    generate_plan_node,
    summarize_agent_trace_node,
)
from src.telemetry.logger import logger

load_dotenv()


# ============================================================
# GLOBAL STATE — Quản lý session state cho Gradio
# ============================================================

class TravelSession:
    """Quản lý state của một phiên planning."""

    def __init__(self):
        self.graph_app = compile_travel_graph()
        self.current_state: dict = None
        self.is_waiting_for_replan = False

    def reset(self):
        """Reset session cho yêu cầu mới."""
        self.current_state = None
        self.is_waiting_for_replan = False


# Global session
session = TravelSession()


# ============================================================
# CHAT HANDLER — Xử lý tin nhắn từ Gradio
# ============================================================

def chat_handler(message: str, chat_history: list[dict]):
    """
    Xử lý tin nhắn từ user (Generator — yield từng chunk).
    """
    logger.log_event("USER_INPUT", {"message": message})

    if session.is_waiting_for_replan and session.current_state:
        yield from handle_replan_response(message)
    else:
        yield from handle_new_request(message, chat_history)


def handle_new_request(user_input: str, chat_history: list[dict]):
    """Chạy pipeline cho yêu cầu du lịch mới. Yield từng chunk khi mỗi node hoàn thành."""
    from src.telemetry.metrics import tracker
    tracker.session_metrics.clear()  # Reset metrics per session
    
    session.reset()
    initial_state = create_initial_state(user_input, chat_history)
    accumulated_state = dict(initial_state)
    all_responses = []

    try:
        for state_update in session.graph_app.stream(initial_state):
            for node_name, node_state in state_update.items():
                logger.log_event("GRAPH_NODE", {"node": node_name})
                accumulated_state.update(node_state)

                # Collect messages from this node and yield immediately as a chunk
                if "messages" in node_state:
                    for msg in node_state["messages"]:
                        if isinstance(msg, tuple) and len(msg) == 2:
                            role, content = msg
                            if role == "assistant":
                                all_responses.append(content)
                                yield "\n\n---\n\n".join(all_responses)

                # Check human-in-the-loop
                if node_state.get("waiting_for_user", False):
                    session.is_waiting_for_replan = True
                    session.current_state = accumulated_state
                    logger.log_event("WAITING_FOR_USER", {"reason": "replan"})
                    return

        session.current_state = accumulated_state

        if not all_responses:
            yield "❓ Không có kết quả. Vui lòng thử lại."

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        yield f"❌ Đã xảy ra lỗi: {str(e)}\n\nVui lòng thử lại hoặc kiểm tra API keys trong file `.env`."


def handle_replan_response(user_response: str):
    """Xử lý phản hồi của user về việc thay đổi kế hoạch."""

    positive_keywords = ["có", "đồng ý", "ok", "yes", "đổi", "thay đổi", "ừ", "oke", "được"]
    negative_keywords = ["không", "no", "giữ", "thôi", "ko", "khỏi"]

    response_lower = user_response.strip().lower()

    if any(kw in response_lower for kw in positive_keywords):
        user_confirmed = True
    elif any(kw in response_lower for kw in negative_keywords):
        user_confirmed = False
    else:
        yield "❓ Tôi chưa hiểu. Vui lòng trả lời **có** hoặc **không** để xác nhận thay đổi kế hoạch."
        return

    session.is_waiting_for_replan = False
    logger.log_event("USER_REPLAN_RESPONSE", {"confirmed": user_confirmed})

    session.current_state["user_confirmed_replan"] = user_confirmed
    session.current_state["waiting_for_user"] = False

    all_responses = []

    try:
        # Run remaining nodes manually (since graph already ended at ask_user_replan)
        remaining_nodes = [
            ("process_replan_response", process_replan_response_node),
            ("search_attractions", search_attractions_node),
            ("calculate_distances", calculate_distances_node),
            ("find_hotels", find_hotels_node),
            ("estimate_budget", estimate_budget_node),
            ("generate_plan", generate_plan_node),
            ("summarize_agent_trace", summarize_agent_trace_node),
        ]

        for node_name, node_func in remaining_nodes:
            logger.log_event("GRAPH_NODE_RESUME", {"node": node_name})
            result = node_func(session.current_state)
            session.current_state.update(result)

            if "messages" in result:
                for msg in result["messages"]:
                    if isinstance(msg, tuple) and msg[0] == "assistant":
                        all_responses.append(msg[1])
                        yield "\n\n---\n\n".join(all_responses)

        if not all_responses:
            yield "✅ Đã hoàn thành nhưng không có kết quả chi tiết."

    except Exception as e:
        logger.error(f"Replan pipeline error: {e}")
        yield f"❌ Lỗi khi tiếp tục kế hoạch: {str(e)}"


# ============================================================
# GRADIO UI — Giao diện Web
# ============================================================

def create_gradio_app() -> gr.Blocks:
    """Tạo Gradio Blocks UI."""

    with gr.Blocks(
        title="🧳 Travel Planner Agent",
    ) as app:

        # ── Header ──
        gr.HTML("""
        <div style="text-align: center; padding: 20px;">
            <h1 class="title-text">🧳 Travel Planner Agent</h1>
            <p style="color: #666; font-size: 1.1em;">
                Trợ lý lên kế hoạch du lịch thông minh — Powered by LangGraph + Gemini
            </p>
        </div>
        """)

        # ── Chatbot ──
        chatbot = gr.Chatbot(
            label="💬 Chat với Travel Agent",
            height=500,
            placeholder="Hãy cho tôi biết bạn muốn đi đâu! 🌍",
            elem_classes=["chatbot-container"],
        )

        # ── Input ──
        with gr.Row():
            msg_input = gr.Textbox(
                label="✍️ Nhập yêu cầu du lịch",
                placeholder='Ví dụ: "Tôi muốn đi Đà Nẵng 3 ngày, budget 5 triệu"',
                scale=4,
                lines=1,
                max_lines=3,
            )
            send_btn = gr.Button("🚀 Gửi", variant="primary", scale=1)

        # ── Quick Examples ──
        gr.Examples(
            examples=[
                "Tôi muốn đi Đà Nẵng 3 ngày, budget 5 triệu",
                "Gia đình 4 người muốn đi Phú Quốc 5 ngày, thích biển, ngân sách 30 triệu",
                "Đi Sapa 2 ngày cuối tuần, khoảng 3 triệu, thích trekking",
                "Du lịch Hội An 2 ngày 1 đêm, budget 2 triệu, thích ẩm thực và văn hóa",
            ],
            inputs=msg_input,
            label="💡 Ví dụ nhanh",
        )

        # ── Info Accordion ──
        with gr.Accordion("ℹ️ Thông tin & Hướng dẫn", open=False):
            gr.Markdown("""
            ### 🔧 Cách sử dụng
            1. Nhập yêu cầu du lịch bằng tiếng Việt
            2. Agent sẽ tự động: **Tìm địa điểm → Kiểm tra thời tiết → Tìm khách sạn → Tính chi phí**
            3. Nếu thời tiết xấu, agent sẽ **hỏi bạn** trước khi thay đổi kế hoạch
            4. Nhận kế hoạch du lịch hoàn chỉnh!

            ### 🛠️ Tech Stack
            - **LLM**: Google Gemini
            - **Orchestration**: LangGraph StateGraph
            - **Weather**: OpenWeatherMap API
            - **Search**: Tavily Search API
            - **Distance**: Google Maps Distance Matrix
            - **Hotels**: SerpApi (Google Hotels)
            - **Budget**: Custom Python Logic
            """)

        # ── Event Handlers ──
        def respond(message: str, chat_history: list[dict]):
            if not message.strip():
                yield "", chat_history
                return

            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": ""})
            yield "", chat_history

            # Yield each chunk as it arrives from the pipeline
            # Note: pass a shallow copy of history minus the current user msg & empty assistant msg
            context_history = chat_history[:-2] 
            for chunk_response in chat_handler(message, context_history):
                chat_history[-1]["content"] = chunk_response
                yield "", chat_history

        # Bind events
        msg_input.submit(respond, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(respond, [msg_input, chatbot], [msg_input, chatbot])

    return app


# ============================================================
# MAIN — Entry point
# ============================================================

if __name__ == "__main__":
    print("🧳 Starting Travel Planner Agent...")
    print("=" * 50)

    required_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }

    optional_keys = {
        "OPENWEATHERMAP_API_KEY": os.getenv("OPENWEATHERMAP_API_KEY"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
        "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY"),
    }

    print("\n📋 API Keys Status:")
    for key, value in required_keys.items():
        status = "✅" if value and "your_" not in value else "❌ MISSING"
        print(f"  {key}: {status}")

    for key, value in optional_keys.items():
        status = "✅" if value and "your_" not in value else "⚠️ Not configured (fallback mode)"
        print(f"  {key}: {status}")

    print("\n" + "=" * 50)

    # Chỉ cần một trong hai key là có thể chạy
    if not (required_keys["GEMINI_API_KEY"] or required_keys["OPENAI_API_KEY"]):
        print("❌ Cần ít nhất OPENAI_API_KEY hoặc GEMINI_API_KEY trong file .env để chạy!")
        exit(1)


    app = create_gradio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="cyan",
            neutral_hue="slate",
        ),
        css="""
        .gradio-container { max-width: 900px !important; margin: auto; }
        .chatbot-container { min-height: 500px; }
        footer { display: none !important; }
        .title-text {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2em;
            font-weight: bold;
        }
        """
    )
