"""
Pydantic Models cho Travel Planning Agent.
Đảm bảo structured output từ LLM và type safety xuyên suốt pipeline.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ============================================================
# Enums
# ============================================================

class ActivityType(str, Enum):
    """Loại hoạt động: trong nhà hoặc ngoài trời."""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    BOTH = "both"


class TransportMode(str, Enum):
    """Phương tiện di chuyển."""
    DRIVING = "driving"
    WALKING = "walking"
    TRANSIT = "transit"
    BICYCLING = "bicycling"


# ============================================================
# Input Models
# ============================================================

class TravelRequest(BaseModel):
    """Yêu cầu du lịch đã được parse từ input tự nhiên của user."""
    destination: str = Field(..., description="Thành phố / địa điểm du lịch, ví dụ: 'Đà Nẵng'")
    days: int = Field(..., ge=1, le=30, description="Số ngày du lịch")
    budget: float = Field(..., gt=0, description="Ngân sách tổng (VNĐ)")
    num_people: int = Field(default=1, ge=1, description="Số người đi")
    preferences: Optional[str] = Field(
        default=None,
        description="Sở thích đặc biệt: biển, núi, văn hóa, ẩm thực, ..."
    )
    transport_mode: TransportMode = Field(
        default=TransportMode.DRIVING,
        description="Phương tiện di chuyển ưu tiên"
    )
    origin: Optional[str] = Field(
        default="Hồ Chí Minh",
        description="Điểm khởi hành, ví dụ: 'Hà Nội' hoặc 'SGN'"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Ngày bắt đầu hành trình (YYYY-MM-DD)"
    )
    intent: str = Field(
        default="plan_trip",
        description="Ý định ở mức điều hướng: 'plan_trip' | 'direct_qa' | 'chat'"
    )
    task: str = Field(
        default="chat",
        description="Nhóm tác vụ: chat | flight_only | hotel_only | attractions_only | weather_only | full_plan"
    )
    reply: Optional[str] = Field(default=None, description="Câu trả lời của bạn gửi cho người dùng...")
    is_enough_info: bool = Field(default=True, description="true nếu đủ thông tin để chạy tác vụ đã phân loại")




# ============================================================
# Tool Output Models
# ============================================================

class WeatherInfo(BaseModel):
    """Thông tin thời tiết tại điểm đến."""
    city: str = Field(..., description="Tên thành phố")
    temperature_celsius: float = Field(..., description="Nhiệt độ trung bình (°C)")
    condition: str = Field(..., description="Mô tả thời tiết: 'Sunny', 'Rainy', 'Cloudy', ...")
    humidity: int = Field(..., ge=0, le=100, description="Độ ẩm (%)")
    is_rainy: bool = Field(..., description="True nếu trời mưa hoặc dự báo mưa")
    forecast_summary: str = Field(
        ..., description="Tóm tắt dự báo thời tiết cho các ngày du lịch"
    )
    wind_speed: Optional[float] = Field(default=None, description="Tốc độ gió (m/s)")
    icon: Optional[str] = Field(default=None, description="Weather icon code từ OpenWeatherMap")
    aqi: Optional[int] = Field(default=None, description="Chỉ số chất lượng không khí (AQI)")
    aqi_description: Optional[str] = Field(default=None, description="Mô tả chất lượng không khí (Tốt, Trung bình, Ô nhiễm...)")



class Attraction(BaseModel):
    """Một địa điểm tham quan."""
    name: str = Field(..., description="Tên địa điểm")
    activity_type: ActivityType = Field(..., description="Loại hoạt động")
    description: str = Field(..., description="Mô tả ngắn gọn")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Đánh giá (0-5 sao)")
    address: Optional[str] = Field(default=None, description="Địa chỉ")
    estimated_visit_hours: Optional[float] = Field(
        default=None, description="Thời gian tham quan ước tính (giờ)"
    )
    entrance_fee: Optional[float] = Field(
        default=None, description="Phí vào cổng (VNĐ), None nếu miễn phí"
    )


class AttractionList(BaseModel):
    """Danh sách địa điểm tham quan tìm được."""
    city: str = Field(..., description="Thành phố tìm kiếm")
    attractions: list[Attraction] = Field(default_factory=list)
    activity_filter: ActivityType = Field(
        default=ActivityType.BOTH,
        description="Bộ lọc loại hoạt động đã áp dụng"
    )


class DistanceResult(BaseModel):
    """Kết quả tính khoảng cách giữa 2 điểm."""
    origin: str = Field(..., description="Điểm xuất phát")
    destination: str = Field(..., description="Điểm đến")
    distance_km: float = Field(..., description="Khoảng cách (km)")
    duration_minutes: float = Field(..., description="Thời gian di chuyển (phút)")
    mode: TransportMode = Field(..., description="Phương tiện di chuyển")


class HotelOption(BaseModel):
    """Một lựa chọn khách sạn."""
    name: str = Field(..., description="Tên khách sạn")
    price_per_night: float = Field(..., description="Giá mỗi đêm (VNĐ)")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="Đánh giá (0-5)")
    address: Optional[str] = Field(default=None, description="Địa chỉ")
    amenities: list[str] = Field(default_factory=list, description="Tiện nghi: WiFi, Pool, ...")
    link: Optional[str] = Field(default=None, description="Link đặt phòng")


class HotelSearchResult(BaseModel):
    """Kết quả tìm kiếm khách sạn."""
    city: str = Field(..., description="Thành phố tìm kiếm")
    check_in: str = Field(..., description="Ngày check-in (YYYY-MM-DD)")
    check_out: str = Field(..., description="Ngày check-out (YYYY-MM-DD)")
    hotels: list[HotelOption] = Field(default_factory=list)


class FlightInfo(BaseModel):
    """Thông tin một chuyến bay."""
    airline: str = Field(..., description="Hãng hàng không")
    flight_number: Optional[str] = Field(default=None, description="Số hiệu chuyến bay")
    departure_time: str = Field(..., description="Thời gian khởi hành")
    arrival_time: str = Field(..., description="Thời gian đến")
    price: float = Field(..., description="Giá vé (VNĐ)")
    origin: str = Field(..., description="Điểm đi")
    destination: str = Field(..., description="Điểm đến")


class FlightSearchResult(BaseModel):
    """Kết quả tìm kiếm chuyến bay."""
    flights: list[FlightInfo] = Field(default_factory=list)
    best_option: Optional[FlightInfo] = Field(default=None, description="Lựa chọn tốt nhất")



class BudgetBreakdown(BaseModel):
    """Chi tiết phân bổ ngân sách: Total = Hotel + (Food × Days) + Transport."""
    hotel_total: float = Field(..., description="Tổng chi phí khách sạn (VNĐ)")
    hotel_per_night: float = Field(..., description="Giá khách sạn mỗi đêm (VNĐ)")
    food_total: float = Field(..., description="Tổng chi phí ăn uống (VNĐ)")
    food_per_day: float = Field(..., description="Chi phí ăn uống mỗi ngày (VNĐ)")
    transport_total: float = Field(..., description="Tổng chi phí di chuyển (VNĐ)")
    activities_total: float = Field(
        default=0, description="Tổng chi phí vé tham quan (VNĐ)"
    )
    grand_total: float = Field(..., description="TỔNG CHI PHÍ (VNĐ)")
    days: int = Field(..., description="Số ngày")
    num_people: int = Field(default=1, description="Số người")
    is_within_budget: bool = Field(..., description="True nếu nằm trong ngân sách")
    remaining_budget: float = Field(..., description="Ngân sách còn dư (VNĐ)")


# ============================================================
# Final Output Model
# ============================================================

class DayPlan(BaseModel):
    """Kế hoạch cho 1 ngày."""
    day_number: int = Field(..., description="Ngày thứ mấy")
    activities: list[str] = Field(default_factory=list, description="Danh sách hoạt động")
    meals: list[str] = Field(default_factory=list, description="Gợi ý ăn uống")
    notes: Optional[str] = Field(default=None, description="Ghi chú thêm")


class TravelPlan(BaseModel):
    """Kế hoạch du lịch hoàn chỉnh — output cuối cùng của Agent."""
    destination: str = Field(..., description="Điểm đến")
    days: int = Field(..., description="Số ngày")
    weather_summary: str = Field(..., description="Tóm tắt thời tiết")
    recommended_activity_type: ActivityType = Field(
        ..., description="Loại hoạt động được đề xuất dựa trên thời tiết"
    )
    attractions: list[Attraction] = Field(default_factory=list, description="Địa điểm tham quan")
    hotel_recommendation: Optional[HotelOption] = Field(
        default=None, description="Khách sạn được đề xuất"
    )
    flight_recommendation: Optional[FlightInfo] = Field(
        default=None, description="Chuyến bay được đề xuất"
    )

    daily_itinerary: list[DayPlan] = Field(
        default_factory=list, description="Lịch trình từng ngày"
    )
    budget: Optional[BudgetBreakdown] = Field(default=None, description="Phân bổ chi phí")
    travel_tips: list[str] = Field(
        default_factory=list, description="Mẹo du lịch hữu ích"
    )
    summary: str = Field(..., description="Tóm tắt kế hoạch bằng tiếng Việt")

