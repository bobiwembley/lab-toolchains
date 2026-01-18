"""
Hotel Search Service with Booking.com API integration
"""
import os
import logging
import requests
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Hotel:
    """Hotel information"""
    name: str
    stars: float
    price_per_night: float
    total_price: float
    address: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    url: Optional[str] = None


class HotelSearchService:
    """Service for searching hotels using Booking.com API"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.booking_api_url = "https://booking-com15.p.rapidapi.com/api/v1"
        self.rapidapi_host = "booking-com15.p.rapidapi.com"
        self.providers = ["booking-com15", "mock"]
        self.timeout = 30  # Augmenté à 30s pour éviter les timeouts
        
        logger.info(f"HotelSearchService initialized with providers: {', '.join(self.providers)}")
        self._initialized = True
    
    def search(self, destination: str, checkin_date: str, checkout_date: str, guests: int = 2) -> List[Hotel]:
        """
        Search for hotels in a destination
        
        Args:
            destination: City name
            checkin_date: Check-in date YYYY-MM-DD
            checkout_date: Check-out date YYYY-MM-DD
            guests: Number of guests
            
        Returns:
            List of Hotel objects
        """
        # Try Booking.com API first
        if self.rapidapi_key:
            try:
                hotels = self._search_with_booking(destination, checkin_date, checkout_date, guests)
                if hotels:
                    return hotels
            except Exception as e:
                logger.error(f"Booking.com API error: {e}")
        
        # Fallback to mock data
        logger.info(f"Using mock data for {destination}")
        return self._get_mock_hotels(destination, checkin_date, checkout_date)
    
    def _search_with_booking(self, destination: str, checkin_date: str, checkout_date: str, guests: int) -> List[Hotel]:
        """Search hotels using Booking.com15 API"""
        logger.info(f"Trying Booking.com15 for {destination}")
        
        # Step 1: Get destination ID
        dest_id, dest_type = self._get_destination_id(destination)
        if not dest_id:
            logger.warning(f"Could not find destination ID for {destination}")
            return []
        
        # Step 2: Search hotels
        search_url = f"{self.booking_api_url}/hotels/searchHotels"
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }
        
        params = {
            "dest_id": dest_id,
            "search_type": dest_type,
            "arrival_date": checkin_date,
            "departure_date": checkout_date,
            "adults": str(guests),
            "room_qty": "1",
            "page_number": "1",
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": "fr",
            "currency_code": "USD"
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Booking.com15 search failed: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        
        if not data.get("status"):
            logger.warning(f"Booking.com15 API returned error: {data.get('message')}")
            return []
        
        hotels = []
        
        # Parse results from booking-com15 structure
        results = data.get("data", {}).get("hotels", [])
        
        # Calculate nights
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        nights = (checkout - checkin).days
        
        for hotel_data in results[:5]:  # Limit to 5 hotels
            try:
                property_data = hotel_data.get("property", {})
                
                # Extract hotel info
                name = property_data.get("name", "Unknown Hotel")
                
                # Get price from priceBreakdown
                price_breakdown = property_data.get("priceBreakdown", {})
                gross_price_data = price_breakdown.get("grossPrice", {})
                total_price = float(gross_price_data.get("value", 0))
                
                # Calculate price per night
                price_per_night = total_price / nights if nights > 0 else total_price
                
                # Stars (propertyClass or accuratePropertyClass)
                stars = float(property_data.get("accuratePropertyClass", property_data.get("propertyClass", 0)))
                
                # Rating
                rating = property_data.get("reviewScore", 0)
                review_count = property_data.get("reviewCount", 0)
                
                # Address (construct from wishlistName or use empty)
                address = property_data.get("wishlistName", destination)
                
                # URL - construct from hotel_id
                hotel_id = hotel_data.get("hotel_id", "")
                url = f"https://www.booking.com/hotel/br/{hotel_id}.html" if hotel_id else None
                
                hotel = Hotel(
                    name=name,
                    stars=stars,
                    price_per_night=price_per_night,
                    total_price=total_price,
                    address=address,
                    rating=rating if rating > 0 else None,
                    review_count=review_count if review_count > 0 else None,
                    url=url
                )
                
                hotels.append(hotel)
                
            except Exception as e:
                logger.warning(f"Error parsing hotel data: {e}")
                continue
        
        if hotels:
            logger.info(f"✅ Booking.com15: Found {len(hotels)} hotels")
        
        return hotels
    
    def _get_destination_id(self, destination: str) -> tuple[Optional[str], str]:
        """Get Booking.com15 destination ID and type for a city"""
        try:
            search_url = f"{self.booking_api_url}/hotels/searchDestination"
            
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": self.rapidapi_host
            }
            
            # Try multiple search variations
            search_terms = [
                destination,  # Original
                destination.split(',')[0].strip(),  # First part if contains comma
                destination.split()[0] if len(destination.split()) > 2 else destination  # First word for long names
            ]
            
            for search_term in search_terms:
                params = {"query": search_term}
                
                logger.info(f"Trying Booking.com15 location search: '{search_term}'")
                response = requests.get(search_url, headers=headers, params=params, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                
                if not data.get("status"):
                    continue
                
                results = data.get("data", [])
                
                # Get first city result
                for item in results:
                    if item.get("dest_type") == "city":
                        dest_id = str(item.get("dest_id"))
                        dest_type = "city"
                        logger.info(f"✅ Found Booking.com15 dest_id: {dest_id} (type: {dest_type}) for '{search_term}'")
                        return dest_id, dest_type
                
                # If no city, try first result
                if results:
                    first = results[0]
                    dest_id = str(first.get("dest_id"))
                    dest_type = first.get("dest_type", "city")
                    logger.info(f"✅ Using first result dest_id: {dest_id} (type: {dest_type}) for '{search_term}'")
                    return dest_id, dest_type
            
            logger.warning(f"No destination ID found for any variation of '{destination}'")
            return None, "city"
            
        except Exception as e:
            logger.error(f"Error getting destination ID: {e}")
            return None, "city"
    
    def _get_mock_hotels(self, destination: str, checkin_date: str, checkout_date: str) -> List[Hotel]:
        """Generate mock hotel data"""
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        nights = (checkout - checkin).days
        
        mock_data = {
            "Havana": [
                {"name": "Hotel Nacional de Cuba", "stars": 4.5, "price": 120, "rating": 8.5},
                {"name": "Melia Cohiba", "stars": 5.0, "price": 180, "rating": 9.0},
                {"name": "Casa Particular Colonial", "stars": 4.0, "price": 45, "rating": 8.8}
            ],
            "New York": [
                {"name": "The Plaza Hotel", "stars": 5.0, "price": 450, "rating": 9.2},
                {"name": "Hampton Inn Manhattan", "stars": 3.5, "price": 220, "rating": 8.3}
            ],
            "Paris": [
                {"name": "Le Bristol Paris", "stars": 5.0, "price": 650, "rating": 9.5},
                {"name": "Hotel du Louvre", "stars": 4.5, "price": 320, "rating": 8.9},
                {"name": "Ibis Paris Centre", "stars": 3.0, "price": 110, "rating": 7.8}
            ],
            "Tokyo": [
                {"name": "The Peninsula Tokyo", "stars": 5.0, "price": 580, "rating": 9.4},
                {"name": "Hotel Gracery Shinjuku", "stars": 4.0, "price": 180, "rating": 8.6}
            ],
            "Rio de Janeiro": [
                {"name": "Belmond Copacabana Palace", "stars": 5.0, "price": 520, "rating": 9.3},
                {"name": "Hilton Copacabana", "stars": 4.5, "price": 280, "rating": 8.7},
                {"name": "Hotel Atlantico Copacabana", "stars": 3.5, "price": 95, "rating": 7.9}
            ]
        }
        
        # Default hotels if destination not found
        default_hotels = [
            {"name": f"Hotel {destination}", "stars": 4.0, "price": 150, "rating": 8.0},
            {"name": f"Grand Hotel {destination}", "stars": 4.5, "price": 220, "rating": 8.5},
            {"name": f"Budget Inn {destination}", "stars": 3.0, "price": 80, "rating": 7.5}
        ]
        
        hotels_data = mock_data.get(destination, default_hotels)
        hotels = []
        
        for data in hotels_data:
            hotel = Hotel(
                name=data["name"],
                stars=data["stars"],
                price_per_night=data["price"],
                total_price=data["price"] * nights,
                address=f"{destination}",
                rating=data.get("rating"),
                review_count=None
            )
            hotels.append(hotel)
        
        return hotels


# Singleton instance
_hotel_service = None

def get_hotel_service() -> HotelSearchService:
    """Get singleton instance of HotelSearchService"""
    global _hotel_service
    if _hotel_service is None:
        _hotel_service = HotelSearchService()
    return _hotel_service
