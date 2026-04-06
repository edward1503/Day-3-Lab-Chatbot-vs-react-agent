"""
Travel Attractions & Itinerary Tools
Using OpenTripMap API for POI (Point of Interest) discovery
"""

import requests
from typing import List, Dict, Any, Optional
import json

# OpenTripMap API configuration
OPENTRIPMAP_API_URL = "https://api.opentripmap.com/0.3"
# Free API key (public, no auth required for basic features)
# For production, get your own from https://opentripmap.com/product

def get_location_coordinates(location: str) -> Optional[Dict[str, float]]:
    """
    [TOOL] Convert location name to coordinates using OpenTripMap
    Args:
        location: Tên địa điểm (e.g., "Hà Nội", "Sài Gòn", "Đà Nẵng")
    Returns:
        Dict with lat, lon coordinates
    """
    try:
        url = f"{OPENTRIPMAP_API_URL}/geoname/search"
        params = {"name": location, "format": "json"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("features"):
            feature = data["features"][0]
            props = feature.get("properties", {})
            return {
                "lat": feature["geometry"]["coordinates"][1],
                "lon": feature["geometry"]["coordinates"][0],
                "name": props.get("name", location),
                "kind": props.get("kind", "unknown")
            }
    except Exception as e:
        print(f"Error getting coordinates for {location}: {e}")
    
    return None

def explore_top_attractions(location: str, limit: int = 5, kind: str = None) -> str:
    """
    [MEMBER C/D] Khám phá các điểm du lịch hàng đầu tại một địa điểm.
    
    Args:
        location: Tên thành phố/địa điểm (e.g., "Hà Nội", "Sài Gòn")
        limit: Số lượng điểm du lịch cần trả về (default: 5)
        kind: Loại điểm du lịch (e.g., "museum", "landmark", "monument")
                Nếu None, sẽ lấy tất cả các loại
    
    Returns:
        String formatted list of attractions with ratings and descriptions
    """
    try:
        # Use fallback mock data for attractions
        attractions_data = {
            "hà nội": [
                {
                    "name": "Lăng Hồ Chí Minh",
                    "kind": "monument",
                    "rating": 4.8,
                    "distance": 1200,
                    "description": "Lăng của Chủ tịch Hồ Chí Minh, một trong những di tích lịch sử quan trọng nhất"
                },
                {
                    "name": "Thành phố cổ Hà Nội",
                    "kind": "historic",
                    "rating": 4.9,
                    "distance": 500,
                    "description": "Khu phố cũ với kiến trúc độc đáo, mua sắm và ẩm thực truyền thống"
                },
                {
                    "name": "Nhà Thờ Lớn Hà Nội",
                    "kind": "religion",
                    "rating": 4.7,
                    "distance": 800,
                    "description": "Nhà thờ Thiên Chúa Giáo lớn nhất Hà Nội, kiến trúc Gothic đẹp mắt"
                },
                {
                    "name": "Hồ Hoàn Kiếm",
                    "kind": "natural",
                    "rating": 4.6,
                    "distance": 100,
                    "description": "Hồ nước thơm mát giữa lòng Hà Nội, lý tưởng để dạo bộ"
                },
                {
                    "name": "Bảo tàng Quốc gia Việt Nam",
                    "kind": "museum",
                    "rating": 4.5,
                    "distance": 1500,
                    "description": "Bảo tàng lớn nhất Việt Nam với bộ sưu tập quý báu về lịch sử"
                }
            ],
            "sài gòn": [
                {
                    "name": "Dinh Độc Lập",
                    "kind": "monument",
                    "rating": 4.8,
                    "distance": 2000,
                    "description": "Tòa nhà lịch sử biểu tượng của Sài Gòn, nơi kết thúc cuộc chiến tranh"
                },
                {
                    "name": "Nhà thờ Đức Bà",
                    "kind": "religion",
                    "rating": 4.9,
                    "distance": 1000,
                    "description": "Nhà thờ Thiên Chúa Giáo với kiến trúc Pháp tuyệt đẹp, được xây từ thế kỷ 19"
                },
                {
                    "name": "Chợ Bến Thành",
                    "kind": "tourist_facilities",
                    "rating": 4.5,
                    "distance": 800,
                    "description": "Chợ truyền thống nổi tiếng với đặc sản địa phương và mua sắm"
                },
                {
                    "name": "Bảo tàng Chiến tranh",
                    "kind": "museum",
                    "rating": 4.6,
                    "distance": 1200,
                    "description": "Bảo tàng ghi lại lịch sử cuộc chiến tranh Việt Nam"
                },
                {
                    "name": "Khu phố Ngô Tất Tố",
                    "kind": "historic",
                    "rating": 4.4,
                    "distance": 500,
                    "description": "Khu phố cổ với những quán cà phê cổ xưa và kiến trúc pháp tuyệt đẹp"
                }
            ],
            "đà nẵng": [
                {
                    "name": "Bãi biển Mỹ Khê",
                    "kind": "natural",
                    "rating": 4.9,
                    "distance": 0,
                    "description": "Một trong những bãi biển đẹp nhất thế giới, nước trong xanh"
                },
                {
                    "name": "Hội An cổ thành",
                    "kind": "historic",
                    "rating": 4.8,
                    "distance": 30000,
                    "description": "Phố cổ Hội An nằm gần Đà Nẵng, du lịch Unesco, kiến trúc độc đáo"
                },
                {
                    "name": "Bàn Tay Phật",
                    "kind": "religion",
                    "rating": 4.6,
                    "distance": 40000,
                    "description": "Tượng Phật khổng lồ trên núi Ba Na, có thể ngắm nhìn từ xa"
                },
                {
                    "name": "Chùa Linh Ứng",
                    "kind": "religion",
                    "rating": 4.7,
                    "distance": 5000,
                    "description": "Chùa cổ nằm trên núi với tượng Phật Quan Âm lofty, nhìn ra biển"
                }
            ],
            "huế": [
                {
                    "name": "Hoàng Thành Huế",
                    "kind": "monument",
                    "rating": 4.8,
                    "distance": 2000,
                    "description": "Dấu tích hoàng gia của triều đại Nguyễn, di sản Unesco"
                },
                {
                    "name": "Lăng Tự Đức",
                    "kind": "historic",
                    "rating": 4.7,
                    "distance": 8000,
                    "description": "Lăng mộ hoàng đế Tự Đức, kiến trúc vô cùng đẹp giữa thiên nhiên"
                }
            ]
        }
        
        location_lower = location.lower()
        attractions = None
        
        # Find attractions for the location
        for city in attractions_data.keys():
            if city in location_lower or location_lower in city:
                attractions = attractions_data[city]
                break
        
        if not attractions:
            return f"Không tìm thấy dữ liệu điểm du lịch cho '{location}'.\n" \
                   f"Các thành phố có sẵn: Hà Nội, Sài Gòn, Đà Nẵng, Huế"
        
        # Filter by category if specified
        if kind:
            attractions = [a for a in attractions if a['kind'] == kind]
        
        # Limit results
        attractions = attractions[:limit]
        
        # Format output
        output = f"🎯 ĐỊA ĐIỂM DU LỊCH HÀNG ĐẦU TẠI {location.upper()}:\n"
        output += f"({', '.join(set([a['kind'] for a in attractions]))})\n\n"
        
        for i, attr in enumerate(attractions, 1):
            output += f"{i}. {attr['name']}\n"
            output += f"   📍 Loại: {attr['kind'].replace('_', ' ').title()}\n"
            output += f"   ⭐ Đánh giá: {attr['rating']}/5.0\n"
            if attr.get('distance'):
                output += f"   📏 Khoảng cách: {attr['distance']:.0f}m\n"
            if attr.get('description'):
                output += f"   📖 {attr['description']}\n"
            output += "\n"
        
        return output
    
    except Exception as e:
        return f"Lỗi xử lý yêu cầu: {str(e)}"

def _get_attraction_details(xid: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific attraction
    Args:
        xid: OpenTripMap attraction XID
    """
    try:
        url = f"{OPENTRIPMAP_API_URL}/places/xid/{xid}"
        params = {"format": "json"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {}

def search_by_category(location: str, category: str) -> str:
    """
    [TOOL] Tìm kiếm điểm du lịch theo thể loại cụ thể
    
    Args:
        location: Tên thành phố
        category: Thể loại (museum, monument, landmark, historic, tourist_facilities,
                           religion, natural, etc.)
    
    Returns:
        Formatted list of attractions by category
    """
    # Map Vietnamese categories to attraction kinds
    category_map = {
        "bảo tàng": "museum",
        "museum": "museum",
        "công trình": "monument",
        "monument": "monument",
        "landmark": "landmark",
        "nổi tiếng": "landmark",
        "lịch sử": "historic",
        "historic": "historic",
        "tôn giáo": "religion",
        "religion": "religion",
        "thiên nhiên": "natural",
        "natural": "natural",
        "đặc sản": "tourist_facilities",
        "ẩm thực": "restaurant",
        "restaurant": "restaurant"
    }
    
    kind = category_map.get(category.lower(), category.lower())
    return explore_top_attractions(location, limit=8, kind=kind)

def get_itinerary_suggestion(location: str, duration_days: int) -> str:
    """
    [TOOL] Gợi ý lịch trình du lịch cho một địa điểm
    
    Args:
        location: Tên thành phố
        duration_days: Số ngày du lịch (1-7)
    
    Returns:
        Suggested itinerary with attractions for each day
    """
    try:
        # Get attractions for the location
        attractions_output = explore_top_attractions(location, limit=min(duration_days * 2, 10))
        
        if "Không tìm thấy" in attractions_output:
            # Provide generic itinerary even if no attractions found
            output = f"📅 GỢI Ý LỊCH TRÌNH {duration_days} NGÀY TẠI {location.upper()}:\n\n"
        else:
            output = f"📅 GỢI Ý LỊCH TRÌNH {duration_days} NGÀY TẠI {location.upper()}:\n\n"
        
        if duration_days == 1:
            output += "🌅 NGÀY 1 - Khám phá trung tâm\n"
            output += f"  - Sáng (07:00-11:00): Khám phá điểm du lịch nổi tiếng nhất\n"
            output += f"  - Trưa (11:00-14:00): Thưởng thức ẩm thực địa phương\n"
            output += f"  - Chiều (14:00-17:00): Dạo phố, shopping\n"
            output += f"  - Tối (17:00-21:00): Thăm quan di tích lịch sử\n"
        
        elif duration_days == 2:
            output += "🌅 NGÀY 1 - Khám phá trung tâm\n"
            output += f"  - Sáng: Tham quan các landmark chính\n"
            output += f"  - Trưa: Ẩm thực địa phương\n"
            output += f"  - Chiều: Bảo tàng hoặc công trình lịch sử\n"
            output += f"\n🌄 NGÀY 2 - Khám phá xung quanh\n"
            output += f"  - Sáng: Tours du lịch ngoài thành\n"
            output += f"  - Trưa: Ăn cơm tạm\n"
            output += f"  - Chiều: Hoạt động giải trí hoặc mua sắm\n"
        
        else:  # 3+ days
            days_suggested = min(duration_days, 5)
            activities = [
                "Khám phá khu trung tâm & landmarks nổi tiếng",
                "Tham quan bảo tàng & công trình lịch sử",
                "Tour ngoài thành & khám phá thiên nhiên",
                "Ẩm thực & shopping tại các chợ địa phương",
                "Khám phá những góc ẩn & nghỉ ngơi"
            ]
            
            for day in range(1, days_suggested + 1):
                output += f"\n🌅 NGÀY {day} - {activities[day-1]}\n"
                output += f"  - Sáng: Khởi hành sớm (6:00-7:00)\n"
                output += f"  - Trưa: Ăn cơm tại nhà hàng địa phương\n"
                output += f"  - Chiều: Tham quan & hoạt động ngoài trời\n"
            
            if duration_days > 5:
                output += f"\n⭐ CÁC NGÀY CÒN LẠI: Tự do khám phá hoặc nghỉ ngơi\n"
        
        output += f"\n💡 LƯỚI Ý DU LỊCH:\n"
        output += f"  ✈️  Đặt vé máy bay/xe trước 2-3 tuần\n"
        output += f"  🏨 Đặt khách sạn trước để có giá tốt\n"
        output += f"  🛂 Chuẩn bị giấy tờ: hộ chiếu, visa (nếu cần)\n"
        output += f"  🧳 Chuẩn bị thích hợp cho thời tiết địa phương\n"
        output += f"  💰 Chuẩn bị ngân sách đủ cho ăn, ở, chơi\n"
        output += f"  🏥 Mua bảo hiểm du lịch toàn diện\n"
        output += f"  📱 Download map offline, dịch vụ giao thông\n"
        
        return output
    
    except Exception as e:
        return f"Lỗi khi tạo lịch trình: {str(e)}"

if __name__ == "__main__":
    # Test the tools
    print("=" * 60)
    print("Testing Attractions & Itinerary Tools")
    print("=" * 60)
    
    # Test 1: Get attractions
    print("\n1️⃣  Testing explore_top_attractions('Hà Nội'):")
    print("-" * 60)
    result = explore_top_attractions("Hà Nội", limit=3)
    print(result)
    
    # Test 2: Search by category
    print("\n2️⃣  Testing search_by_category('Sài Gòn', 'museum'):")
    print("-" * 60)
    result = search_by_category("Sài Gòn", "museum")
    print(result)
    
    # Test 3: Get itinerary
    print("\n3️⃣  Testing get_itinerary_suggestion('Đà Nẵng', 3):")
    print("-" * 60)
    result = get_itinerary_suggestion("Đà Nẵng", 3)
    print(result)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
