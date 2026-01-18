"""
Airport Code Service - Convert city names to IATA airport codes
Uses Amadeus API for real-time lookup
"""
import os
import logging
from typing import Optional, Dict
from amadeus import Client, ResponseError

logger = logging.getLogger(__name__)


class AirportCodeService:
    """Service for finding IATA airport codes from city names"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.amadeus_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_secret = os.getenv("AMADEUS_API_SECRET")
        
        if self.amadeus_key and self.amadeus_secret:
            try:
                self.amadeus = Client(
                    client_id=self.amadeus_key,
                    client_secret=self.amadeus_secret
                )
                logger.info("✅ AirportCodeService initialized with Amadeus API")
            except Exception as e:
                logger.warning(f"Failed to initialize Amadeus: {e}")
                self.amadeus = None
        else:
            logger.warning("Amadeus credentials missing")
            self.amadeus = None
            
        # Fallback mapping for common cities (used only if API fails)
        self.fallback_codes = {
            "paris": "CDG",
            "rio de janeiro": "GIG",
            "rio": "GIG",
            "tokyo": "NRT",
            "osaka": "KIX",  # Kansai International Airport
            "new york": "JFK",
            "londres": "LHR",
            "london": "LHR",
            "dubai": "DXB",
            "sydney": "SYD",
            "bangkok": "BKK",
            "singapore": "SIN",
            "singapour": "SIN",
            "hong kong": "HKG",
            "la havane": "HAV",
            "havana": "HAV",
            "barcelone": "BCN",
            "barcelona": "BCN",
            "rome": "FCO",
            "roma": "FCO",
            "madrid": "MAD",
            "amsterdam": "AMS",
            "lisbonne": "LIS",
            "lisbon": "LIS",
            "berlin": "TXL",
            "marrakech": "RAK",
            "le caire": "CAI",
            "cairo": "CAI",
            "istanbul": "IST",
            "moscou": "SVO",
            "moscow": "SVO",
            "mumbai": "BOM",
            "delhi": "DEL",
            "shanghai": "PVG",
            "beijing": "PEK",
            "pekin": "PEK",
            "los angeles": "LAX",
            "san francisco": "SFO",
            "chicago": "ORD",
            "miami": "MIA",
            "toronto": "YYZ",
            "montreal": "YUL",
            "mexico": "MEX",
            "buenos aires": "EZE",
            "sao paulo": "GRU",
            "johannesburg": "JNB",
        }
        
        self._initialized = True
    
    def get_airport_code(self, city_name: str) -> Dict[str, str]:
        """
        Get IATA airport code for a city
        
        Args:
            city_name: Name of the city (e.g., "Rio de Janeiro", "Tokyo")
            
        Returns:
            Dict with 'code', 'name', 'city', 'country'
        """
        # Normalize city name
        city_normalized = city_name.strip().lower()
        
        # Try Amadeus API first
        if self.amadeus:
            try:
                result = self._search_with_amadeus(city_name)
                if result:
                    logger.info(f"✅ Found airport code via Amadeus: {city_name} → {result['code']}")
                    return result
            except Exception as e:
                logger.warning(f"Amadeus API error: {e}")
        
        # Fallback to local mapping
        if city_normalized in self.fallback_codes:
            code = self.fallback_codes[city_normalized]
            logger.info(f"✅ Found airport code via fallback: {city_name} → {code}")
            return {
                "code": code,
                "name": f"{city_name} Airport",
                "city": city_name,
                "country": "Unknown"
            }
        
        # If still not found, return None
        logger.warning(f"❌ Could not find airport code for: {city_name}")
        return None
    
    def _search_with_amadeus(self, city_name: str) -> Optional[Dict[str, str]]:
        """Search airport code using Amadeus Location API"""
        try:
            # Use Amadeus Reference Data - Locations API
            response = self.amadeus.reference_data.locations.get(
                keyword=city_name,
                subType='AIRPORT,CITY'
            )
            
            if not response.data:
                return None
            
            # Get first result (usually the main airport)
            location = response.data[0]
            
            return {
                "code": location['iataCode'],
                "name": location.get('name', ''),
                "city": location.get('address', {}).get('cityName', city_name),
                "country": location.get('address', {}).get('countryName', '')
            }
            
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return None


# Singleton instance
_airport_service = None

def get_airport_service() -> AirportCodeService:
    """Get or create the singleton airport service instance"""
    global _airport_service
    if _airport_service is None:
        _airport_service = AirportCodeService()
    return _airport_service
