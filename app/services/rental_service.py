"""
Vacation Rentals Service with multi-provider fallback
SerpAPI → RapidAPI Airbnb → Mock Data
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


@dataclass
class VacationRental:
    """Structured vacation rental data model"""
    name: str
    type: str  # "apartment", "house", "villa", etc.
    bedrooms: int
    price_per_night: float
    total_price: float
    currency: str
    rating: float
    location: str
    amenities: List[str]
    
    @property
    def amenities_formatted(self) -> str:
        """Format amenities for display"""
        if not self.amenities:
            return "Aucun équipement listé"
        return ", ".join(self.amenities[:3])


class VacationRentalService:
    """
    Multi-provider vacation rental service
    Fallback: SerpAPI → RapidAPI → Mock Data
    """
    
    def __init__(
        self,
        serpapi_key: Optional[str] = None,
        rapidapi_key: Optional[str] = None
    ):
        """
        Initialize vacation rental service
        
        Args:
            serpapi_key: SerpAPI key (optional, will use env var)
            rapidapi_key: RapidAPI key (optional, will use env var)
        """
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')
        self.rapidapi_key = rapidapi_key or os.getenv('RAPIDAPI_KEY')
        
        # Determine which providers are available
        self.providers = []
        if self.serpapi_key:
            self.providers.append('serpapi')
        if self.rapidapi_key:
            self.providers.append('rapidapi')
        self.providers.append('mock')  # Always available as fallback
        
        logger.info(f"VacationRentalService initialized with providers: {', '.join(self.providers)}")
    
    def search_rentals(
        self,
        destination: str,
        checkin_date: str,
        checkout_date: str,
        guests: int = 2
    ) -> List[VacationRental]:
        """
        Search vacation rentals with automatic fallback
        
        Args:
            destination: City or location name
            checkin_date: Check-in date (YYYY-MM-DD)
            checkout_date: Check-out date (YYYY-MM-DD)
            guests: Number of guests
        
        Returns:
            List of VacationRental objects
        """
        # Try SerpAPI first
        if 'serpapi' in self.providers:
            try:
                logger.info(f"Trying SerpAPI for {destination}")
                rentals = self._search_with_serpapi(destination, checkin_date, checkout_date, guests)
                if rentals:
                    logger.info(f"✅ SerpAPI: Found {len(rentals)} rentals")
                    return rentals
            except Exception as e:
                logger.warning(f"SerpAPI failed: {e}")
        
        # Try RapidAPI Airbnb as fallback
        if 'rapidapi' in self.providers:
            try:
                logger.info(f"Trying RapidAPI Airbnb for {destination}")
                rentals = self._search_with_rapidapi(destination, checkin_date, checkout_date, guests)
                if rentals:
                    logger.info(f"✅ RapidAPI: Found {len(rentals)} rentals")
                    return rentals
            except Exception as e:
                logger.warning(f"RapidAPI failed: {e}")
        
        # Fallback to mock data
        logger.info(f"Using mock data for {destination}")
        return self._get_mock_rentals(destination, checkin_date, checkout_date)
    
    def _search_with_serpapi(
        self,
        destination: str,
        checkin: str,
        checkout: str,
        guests: int
    ) -> List[VacationRental]:
        """Search using SerpAPI Google Hotels (vacation rentals filter)"""
        from serpapi import GoogleSearch
        from datetime import datetime
        
        nights = self._calculate_nights(checkin, checkout)
        
        params = {
            "engine": "google_hotels",
            "q": f"vacation rentals {destination}",
            "check_in_date": checkin,
            "check_out_date": checkout,
            "adults": guests,
            "property_types": "8",  # Vacation rentals
            "currency": "USD",
            "api_key": self.serpapi_key
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        rentals = []
        for property_data in results.get('properties', [])[:5]:
            rental = self._parse_serpapi_rental(property_data, nights, destination)
            if rental:
                rentals.append(rental)
        
        return rentals
    
    def _search_with_rapidapi(
        self,
        destination: str,
        checkin: str,
        checkout: str,
        guests: int
    ) -> List[VacationRental]:
        """Search using RapidAPI Airbnb"""
        import requests
        
        nights = self._calculate_nights(checkin, checkout)
        
        url = "https://airbnb13.p.rapidapi.com/search-location"
        
        querystring = {
            "location": destination,
            "checkin": checkin,
            "checkout": checkout,
            "adults": str(guests),
            "currency": "USD"
        }
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "airbnb13.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        rentals = []
        for listing in data.get('results', [])[:5]:
            rental = self._parse_rapidapi_rental(listing, nights, destination)
            if rental:
                rentals.append(rental)
        
        return rentals
    
    def _parse_serpapi_rental(
        self,
        property_data: dict,
        nights: int,
        destination: str
    ) -> Optional[VacationRental]:
        """Parse SerpAPI property data into VacationRental"""
        try:
            price_per_night = float(property_data.get('rate_per_night', {}).get('extracted_lowest', 0))
            total_price = price_per_night * nights
            
            return VacationRental(
                name=property_data.get('name', 'Property'),
                type=property_data.get('type', 'apartment'),
                bedrooms=2,  # Not always in SerpAPI response
                price_per_night=price_per_night,
                total_price=total_price,
                currency='USD',
                rating=float(property_data.get('overall_rating', 4.0)),
                location=destination,
                amenities=property_data.get('amenities', [])[:3]
            )
        except Exception as e:
            logger.warning(f"Failed to parse SerpAPI rental: {e}")
            return None
    
    def _parse_rapidapi_rental(
        self,
        listing: dict,
        nights: int,
        destination: str
    ) -> Optional[VacationRental]:
        """Parse RapidAPI Airbnb listing into VacationRental"""
        try:
            price_per_night = float(listing.get('price', {}).get('rate', 0))
            total_price = price_per_night * nights
            
            return VacationRental(
                name=listing.get('name', 'Airbnb Property'),
                type=listing.get('type', 'apartment'),
                bedrooms=int(listing.get('bedrooms', 2)),
                price_per_night=price_per_night,
                total_price=total_price,
                currency='USD',
                rating=float(listing.get('rating', 4.5)),
                location=destination,
                amenities=listing.get('amenities', [])[:3]
            )
        except Exception as e:
            logger.warning(f"Failed to parse RapidAPI rental: {e}")
            return None
    
    def _get_mock_rentals(
        self,
        destination: str,
        checkin: str,
        checkout: str
    ) -> List[VacationRental]:
        """Fallback mock data for development"""
        nights = self._calculate_nights(checkin, checkout)
        
        mock_data = {
            "Havana": [
                VacationRental(
                    name="Casa Colonial Centro Habana",
                    type="apartment",
                    bedrooms=2,
                    price_per_night=65,
                    total_price=65 * nights,
                    currency="USD",
                    rating=4.8,
                    location="Centro Habana",
                    amenities=["WiFi", "Climatisation", "Cuisine équipée"]
                ),
                VacationRental(
                    name="Appartement Vue Océan Malecon",
                    type="apartment",
                    bedrooms=1,
                    price_per_night=55,
                    total_price=55 * nights,
                    currency="USD",
                    rating=4.6,
                    location="Vedado",
                    amenities=["WiFi", "Terrasse", "Vue mer"]
                ),
                VacationRental(
                    name="Villa Coloniale avec Jardin",
                    type="house",
                    bedrooms=3,
                    price_per_night=120,
                    total_price=120 * nights,
                    currency="USD",
                    rating=4.9,
                    location="Miramar",
                    amenities=["Piscine", "Jardin", "Parking"]
                ),
            ],
            "New York": [
                VacationRental(
                    name="Manhattan Studio Moderne",
                    type="apartment",
                    bedrooms=1,
                    price_per_night=180,
                    total_price=180 * nights,
                    currency="USD",
                    rating=4.5,
                    location="Midtown",
                    amenities=["WiFi", "Cuisine", "Ascenseur"]
                ),
            ]
        }
        
        return mock_data.get(destination, [])
    
    def _calculate_nights(self, checkin: str, checkout: str) -> int:
        """Calculate number of nights"""
        from datetime import datetime
        try:
            checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_dt = datetime.strptime(checkout, "%Y-%m-%d")
            return (checkout_dt - checkin_dt).days
        except:
            return 7  # Default
    
    def format_rentals_for_display(self, rentals: List[VacationRental]) -> str:
        """Format rental list for user-friendly display"""
        if not rentals:
            return "Aucune location trouvée"
        
        result = []
        for i, rental in enumerate(rentals, 1):
            result.append(
                f"{i}. {rental.name} - {rental.type.upper()}\n"
                f"   💰 ${rental.price_per_night}/nuit • Total: ${rental.total_price}\n"
                f"   🛏️  {rental.bedrooms} chambre(s) • ⭐ {rental.rating}/5\n"
                f"   📍 {rental.location}\n"
                f"   ✨ {rental.amenities_formatted}"
            )
        
        cheapest = min(rentals, key=lambda r: r.total_price)
        result.append(
            f"\n💰 Meilleur prix: ${cheapest.total_price} - {cheapest.name}"
        )
        
        return "\n\n".join(result)


# Singleton instance
_rental_service_instance: Optional[VacationRentalService] = None


def get_rental_service() -> VacationRentalService:
    """Get singleton instance of VacationRentalService"""
    global _rental_service_instance
    if _rental_service_instance is None:
        _rental_service_instance = VacationRentalService()
    return _rental_service_instance
