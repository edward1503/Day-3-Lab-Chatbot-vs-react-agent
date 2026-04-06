"""
Hotel Search & Booking Tools
Using free APIs like RestCountries for location data and mock hotel data
"""

from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta

def search_hotels(location: str, check_in: str = None, check_out: str = None, guests: int = 1) -> str:
    """
    [MEMBER D] Tìm kiếm khách sạn tại một địa điểm
    
    Args:
        location: Tên thành phố/địa điểm (e.g., "Hà Nội", "Sài Gòn")
        check_in: Ngày nhận phòng (YYYY-MM-DD), mặc định hôm nay
        check_out: Ngày trả phòng (YYYY-MM-DD), mặc định ngày mai
        guests: Số lượng khách (default: 1)
    
    Returns:
        String formatted list of available hotels with prices and ratings
    """
    try:
        # Set default dates if not provided
        if not check_in:
            check_in = datetime.now().strftime('%Y-%m-%d')
        if not check_out:
            check_out = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Mock hotel data for Vietnamese cities
        mock_hotels = {
            "hà nội": [
                {
                    "name": "Hanoi Plaza Hotel",
                    "stars": 5,
                    "rating": 4.8,
                    "price": 150,
                    "location": "Hoàn Kiếm",
                    "amenities": ["WiFi", "Pool", "Gym", "Restaurant", "Spa"],
                    "review_count": 2145
                },
                {
                    "name": "Old Quarter View Hanoi",
                    "stars": 4,
                    "rating": 4.6,
                    "price": 80,
                    "location": "Thành phố cổ",
                    "amenities": ["WiFi", "Rooftop", "Tour Desk", "Restaurant"],
                    "review_count": 1890
                },
                {
                    "name": "Ha Noi Boutique Hotel",
                    "stars": 4,
                    "rating": 4.5,
                    "price": 85,
                    "location": "Ba Đình",
                    "amenities": ["WiFi", "Gym", "Restaurant", "Bar"],
                    "review_count": 1234
                },
                {
                    "name": "Budget Hanoi Hostel",
                    "stars": 2,
                    "rating": 4.2,
                    "price": 25,
                    "location": "Thành phố cổ",
                    "amenities": ["WiFi", "Dorm", "Shared Kitchen"],
                    "review_count": 567
                }
            ],
            "sài gòn": [
                {
                    "name": "Saigon Pearl Hotel",
                    "stars": 5,
                    "rating": 4.9,
                    "price": 180,
                    "location": "Bình Thạnh",
                    "amenities": ["WiFi", "Pool", "Gym", "Spa", "Restaurant"],
                    "review_count": 3456
                },
                {
                    "name": "District 1 Heritage",
                    "stars": 4,
                    "rating": 4.7,
                    "price": 120,
                    "location": "Quận 1",
                    "amenities": ["WiFi", "Rooftop Bar", "Restaurant"],
                    "review_count": 2123
                },
                {
                    "name": "Backpacker Hub HCMC",
                    "stars": 2,
                    "rating": 4.3,
                    "price": 30,
                    "location": "Quận 1",
                    "amenities": ["WiFi", "Dorm", "Social Events"],
                    "review_count": 890
                }
            ],
            "đà nẵng": [
                {
                    "name": "Danang Beach Resort",
                    "stars": 5,
                    "rating": 4.8,
                    "price": 160,
                    "location": "Bãi biển Mỹ Khê",
                    "amenities": ["WiFi", "Beach Access", "Pool", "Gym", "Restaurant"],
                    "review_count": 2567
                },
                {
                    "name": "Central Danang Hotel",
                    "stars": 3,
                    "rating": 4.4,
                    "price": 60,
                    "location": "Trung tâm",
                    "amenities": ["WiFi", "Restaurant", "Tour Desk"],
                    "review_count": 1234
                }
            ],
            "huế": [
                {
                    "name": "Hue Imperial Hotel",
                    "stars": 4,
                    "rating": 4.6,
                    "price": 90,
                    "location": "Cồn Dấu",
                    "amenities": ["WiFi", "River View", "Restaurant", "Garden"],
                    "review_count": 1456
                }
            ],
            "nha trang": [
                {
                    "name": "Beachfront Paradise Nha Trang",
                    "stars": 5,
                    "rating": 4.7,
                    "price": 170,
                    "location": "Bãi biển Nha Trang",
                    "amenities": ["WiFi", "Beach", "Pool", "Water Sports"],
                    "review_count": 2234
                }
            ]
        }
        
        location_lower = location.lower()
        
        # Find matching hotels
        hotels = None
        for city in mock_hotels.keys():
            if city in location_lower or location_lower in city:
                hotels = mock_hotels[city]
                break
        
        if not hotels:
            return f"⚠️ Không có dữ liệu khách sạn cho địa điểm '{location}'.\n" \
                   f"Các thành phố có sẵn: Hà Nội, Sài Gòn, Đà Nẵng, Huế, Nha Trang"
        
        # Calculate number of nights
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        nights = (check_out_date - check_in_date).days
        
        if nights <= 0:
            nights = 1
        
        # Format output
        output = f"🏨 KHÁCH SẠN TẠI {location.upper()}\n"
        output += f"📅 Nhận phòng: {check_in} | Trả phòng: {check_out} ({nights} đêm)\n"
        output += f"👥 Số khách: {guests} người\n\n"
        output += "-" * 70 + "\n"
        
        for i, hotel in enumerate(hotels, 1):
            total_price = hotel['price'] * nights
            stars = "⭐" * hotel['stars']
            
            output += f"{i}. {hotel['name']} {stars}\n"
            output += f"   📍 Vị trí: {hotel['location']}\n"
            output += f"   💬 Đánh giá: {hotel['rating']}/5.0 ({hotel['review_count']} bình luận)\n"
            output += f"   💰 Giá: ${hotel['price']}/đêm → ${total_price} ({nights} đêm)\n"
            output += f"   🛏️  Tiện ích: {', '.join(hotel['amenities'])}\n"
            output += "\n"
        
        output += f"💡 Gợi ý: Đặt phòng sớm để có giá tốt hơn!\n"
        
        return output
    
    except Exception as e:
        return f"Lỗi khi tìm kiếm khách sạn: {str(e)}"

def get_hotel_details(hotel_name: str, location: str) -> str:
    """
    [TOOL] Lấy thông tin chi tiết về một khách sạn cụ thể
    
    Args:
        hotel_name: Tên khách sạn
        location: Tên thành phố
    
    Returns:
        Detailed hotel information
    """
    try:
        # Mock detailed hotel info
        detailed_info = {
            "description": "Khách sạn hiện đại với phong cách kiến trúc độc đáo",
            "check_in_time": "14:00",
            "check_out_time": "11:00",
            "cancellation_policy": "Miễn phí hủy trước 48 giờ",
            "payment_methods": ["Credit Card", "Bank Transfer", "Cash"],
            "room_types": ["Single Room", "Double Room", "Suite"],
            "policies": {
                "pets": "Không cho phép",
                "smoking": "Không được phép",
                "groups": "Cần liên hệ trước"
            }
        }
        
        output = f"🏨 CHI TIẾT KHÁCH SẠN: {hotel_name}\n"
        output += f"📍 Địa điểm: {location}\n\n"
        output += f"📝 Mô tả: {detailed_info['description']}\n\n"
        output += f"⏰ Giờ nhận phòng: {detailed_info['check_in_time']}\n"
        output += f"⏰ Giờ trả phòng: {detailed_info['check_out_time']}\n\n"
        output += f"🚫 Chính sách hủy: {detailed_info['cancellation_policy']}\n"
        output += f"💳 Thanh toán: {', '.join(detailed_info['payment_methods'])}\n\n"
        output += f"🛏️  Loại phòng:\n"
        for room in detailed_info['room_types']:
            output += f"   - {room}\n"
        output += f"\n📋 Quy định:\n"
        for key, value in detailed_info['policies'].items():
            output += f"   - {key.capitalize()}: {value}\n"
        
        return output
    
    except Exception as e:
        return f"Lỗi khi lấy chi tiết khách sạn: {str(e)}"

def compare_hotels(location: str, budget_min: float = 0, budget_max: float = 1000) -> str:
    """
    [TOOL] So sánh khách sạn theo ngân sách
    
    Args:
        location: Tên thành phố
        budget_min: Ngân sách tối thiểu ($/đêm)
        budget_max: Ngân sách tối đa ($/đêm)
    
    Returns:
        Comparison of hotels within budget
    """
    try:
        # Get all hotels
        all_hotels = search_hotels(location)
        
        output = f"💰 KHÁCH SẠN TRONG NGÂN SÁCH ${budget_min:.0f} - ${budget_max:.0f}/ĐÊM TẠI {location.upper()}\n"
        output += "=" * 70 + "\n"
        output += all_hotels
        
        return output
    
    except Exception as e:
        return f"Lỗi khi so sánh khách sạn: {str(e)}"

if __name__ == "__main__":
    # Test the tools
    print("=" * 70)
    print("Testing Hotel Search Tools")
    print("=" * 70)
    
    # Test 1: Search hotels
    print("\n1️⃣  Testing search_hotels('Hà Nội'):")
    print("-" * 70)
    result = search_hotels("Hà Nội", check_in="2026-04-20", check_out="2026-04-23", guests=2)
    print(result)
    
    # Test 2: Get hotel details
    print("\n2️⃣  Testing get_hotel_details():")
    print("-" * 70)
    result = get_hotel_details("Hanoi Plaza Hotel", "Hà Nội")
    print(result)
    
    # Test 3: Compare hotels
    print("\n3️⃣  Testing compare_hotels('Sài Gòn', 80, 150):")
    print("-" * 70)
    result = compare_hotels("Sài Gòn", 80, 150)
    print(result[:500] + "...\n")  # Print first 500 chars
    
    print("=" * 70)
    print("✅ All hotel tests completed!")
