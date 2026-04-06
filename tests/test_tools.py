"""
Unit Tests cho Travel Planning Agent.
Chạy: pytest tests/test_tools.py -v
"""

import pytest
from src.schemas.models import (
    TravelRequest,
    WeatherInfo,
    Attraction,
    AttractionList,
    DistanceResult,
    HotelOption,
    HotelSearchResult,
    BudgetBreakdown,
    TravelPlan,
    DayPlan,
    ActivityType,
    TransportMode,
)


# ============================================================
# Test Pydantic Models — Đảm bảo models validate đúng
# ============================================================

class TestPydanticModels:
    """Test tất cả Pydantic models."""

    def test_travel_request_valid(self):
        req = TravelRequest(
            destination="Đà Nẵng",
            days=3,
            budget=5_000_000,
            num_people=2,
            preferences="biển",
            transport_mode=TransportMode.DRIVING,
        )
        assert req.destination == "Đà Nẵng"
        assert req.days == 3
        assert req.budget == 5_000_000

    def test_travel_request_defaults(self):
        req = TravelRequest(
            destination="Hà Nội",
            days=2,
            budget=3_000_000,
        )
        assert req.num_people == 1
        assert req.transport_mode == TransportMode.DRIVING
        assert req.preferences is None

    def test_travel_request_invalid_days(self):
        with pytest.raises(Exception):
            TravelRequest(destination="X", days=0, budget=1000)

    def test_weather_info(self):
        weather = WeatherInfo(
            city="Đà Nẵng",
            temperature_celsius=28.5,
            condition="Clear",
            humidity=70,
            is_rainy=False,
            forecast_summary="Thời tiết đẹp",
        )
        assert weather.is_rainy is False
        assert weather.temperature_celsius == 28.5

    def test_attraction(self):
        attr = Attraction(
            name="Bà Nà Hills",
            activity_type=ActivityType.OUTDOOR,
            description="Khu du lịch nổi tiếng",
            rating=4.5,
        )
        assert attr.activity_type == ActivityType.OUTDOOR

    def test_budget_breakdown(self):
        budget = BudgetBreakdown(
            hotel_total=1_000_000,
            hotel_per_night=500_000,
            food_total=900_000,
            food_per_day=300_000,
            transport_total=200_000,
            activities_total=100_000,
            grand_total=2_200_000,
            days=3,
            num_people=1,
            is_within_budget=True,
            remaining_budget=2_800_000,
        )
        assert budget.grand_total == 2_200_000
        assert budget.is_within_budget is True

    def test_travel_plan(self):
        plan = TravelPlan(
            destination="Đà Nẵng",
            days=3,
            weather_summary="Thời tiết đẹp",
            recommended_activity_type=ActivityType.OUTDOOR,
            summary="Kế hoạch du lịch Đà Nẵng 3 ngày",
        )
        assert plan.destination == "Đà Nẵng"
        assert plan.attractions == []
        assert plan.daily_itinerary == []


# ============================================================
# Test Tools — Kiểm tra tools hoạt động đúng
# ============================================================

class TestBudgetTool:
    """Test budget_tool.py — đã implement đầy đủ."""

    def test_estimate_budget_basic(self):
        from src.tools.budget_tool import estimate_budget
        result = estimate_budget(
            hotel_price_per_night=500_000,
            days=3,
            num_people=1,
            total_budget=5_000_000,
        )
        # Hotel: 500k * 2 đêm = 1,000,000
        assert result.hotel_total == 1_000_000
        # Food: 300k * 3 ngày * 1 người = 900,000
        assert result.food_total == 900_000
        # Transport: 0 (mặc định)
        assert result.transport_total == 0
        # Total = 1,000,000 + 900,000 = 1,900,000
        assert result.grand_total == 1_900_000
        assert result.is_within_budget is True
        assert result.remaining_budget == 3_100_000

    def test_estimate_budget_over_budget(self):
        from src.tools.budget_tool import estimate_budget
        result = estimate_budget(
            hotel_price_per_night=2_000_000,
            days=3,
            num_people=2,
            total_budget=3_000_000,
        )
        # Hotel: 2M * 2 = 4M
        # Food: 300k * 3 * 2 = 1.8M
        # Total = 5.8M > 3M
        assert result.is_within_budget is False
        assert result.remaining_budget < 0

    def test_estimate_budget_with_attractions(self):
        from src.tools.budget_tool import estimate_budget
        attractions = [
            Attraction(
                name="Test",
                activity_type=ActivityType.OUTDOOR,
                description="Test",
                entrance_fee=100_000,
            ),
        ]
        result = estimate_budget(
            hotel_price_per_night=500_000,
            days=2,
            num_people=2,
            attractions=attractions,
            total_budget=5_000_000,
        )
        # Activities: 100k * 2 người = 200k
        assert result.activities_total == 200_000


class TestWeatherTool:
    """Test weather_tool.py — kiểm tra raise ValueError khi thiếu API key."""

    def test_get_weather_missing_key(self):
        import os
        # Lưu giá trị cũ
        old_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        os.environ["OPENWEATHERMAP_API_KEY"] = "your_openweathermap_key_here"

        from src.tools.weather_tool import get_weather_forecast
        # Reload module để nhận key mới
        import importlib
        import src.tools.weather_tool as wt
        importlib.reload(wt)

        with pytest.raises(ValueError, match="Chưa cấu hình"):
            wt.get_weather_forecast("Đà Nẵng", days=3)

        # Khôi phục
        if old_key:
            os.environ["OPENWEATHERMAP_API_KEY"] = old_key


# ============================================================
# Test Prompts
# ============================================================

class TestPrompts:
    """Test prompt formatting functions."""

    def test_format_parse_prompt(self):
        from src.prompts.prompt import format_parse_prompt
        prompt = format_parse_prompt("Tôi muốn đi Đà Nẵng 3 ngày")
        assert "Đà Nẵng" in prompt
        assert "3 ngày" in prompt

    def test_format_replan_prompt(self):
        from src.prompts.prompt import format_replan_prompt
        prompt = format_replan_prompt(
            destination="Đà Nẵng",
            weather_condition="Rain",
            temperature=25.0,
            humidity=90,
        )
        assert "Đà Nẵng" in prompt
        assert "Rain" in prompt

    def test_system_prompt_is_vietnamese(self):
        from src.prompts.prompt import SYSTEM_PROMPT
        assert "tiếng Việt" in SYSTEM_PROMPT

    def test_parse_examples_exist(self):
        from src.prompts.prompt import PARSE_EXAMPLES
        assert len(PARSE_EXAMPLES) >= 3
        assert all("input" in ex and "output" in ex for ex in PARSE_EXAMPLES)

    def test_format_final_plan_prompt(self):
        from src.prompts.prompt import format_final_plan_prompt
        prompt = format_final_plan_prompt(
            weather_info="Sunny",
            attractions_info="[]",
            distances_info="[]",
            hotels_info="[]",
            budget_info="{}",
            destination="Test",
            days=2,
            num_people=1,
            budget=1_000_000,
        )
        assert "Test" in prompt
        assert "1,000,000" in prompt


# ============================================================
# Test Graph Build
# ============================================================

class TestTravelGraph:
    """Test LangGraph build."""

    def test_build_graph_no_error(self):
        from src.agent.travel_graph import build_travel_graph
        graph = build_travel_graph()
        assert graph is not None

    def test_compile_graph_no_error(self):
        from src.agent.travel_graph import compile_travel_graph
        app = compile_travel_graph()
        assert app is not None

    def test_create_initial_state(self):
        from src.agent.state import create_initial_state
        state = create_initial_state("Đi Đà Nẵng 3 ngày")
        assert state["user_request"] == "Đi Đà Nẵng 3 ngày"
        assert state["travel_request"] is None
        assert state["needs_replanning"] is False
        assert state["waiting_for_user"] is False
        assert isinstance(state, dict)


# ============================================================
# Test Logger / Telemetry
# ============================================================

class TestTelemetry:
    """Test telemetry logging."""

    def test_logger_log_event(self):
        from src.telemetry.logger import logger
        # Should not raise
        logger.log_event("TEST_EVENT", {"key": "value", "number": 42})

    def test_logger_handles_pydantic(self):
        from src.telemetry.logger import logger
        req = TravelRequest(destination="Test", days=1, budget=1000)
        # Should not raise — logger should serialize Pydantic models
        logger.log_event("TEST_PYDANTIC", {"request": req})

    def test_logger_handles_enum(self):
        from src.telemetry.logger import logger
        # Enums should be serialized to their value
        logger.log_event("TEST_ENUM", {"type": ActivityType.INDOOR})

    def test_tracker_track_request(self):
        from src.telemetry.metrics import tracker
        tracker.track_request(
            provider="google",
            model="gemini-2.5-flash",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=500,
        )
        assert len(tracker.session_metrics) > 0
