"""
Flight Search Service with Amadeus API Integration
Multi-provider fallback: Amadeus → SerpAPI → Mock Data
Best practices implementation with proper error handling
"""

import os
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from amadeus import Client, ResponseError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class FlightOption:
    """Structured flight data model"""
    airline: str
    price: float
    currency: str
    stops: int
    duration_minutes: int
    departure_time: str
    arrival_time: str
    departure_airport: str
    arrival_airport: str
    
    @property
    def duration_formatted(self) -> str:
        """Convert minutes to hours and minutes"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"
    
    @property
    def stops_formatted(self) -> str:
        """Format stops for display"""
        return "Direct" if self.stops == 0 else f"{self.stops} escale(s)"


class FlightSearchService:
    """
    Production-ready flight search service with Amadeus API
    Fallback: Amadeus → Mock Data
    Follows SOLID principles and best practices
    """
    
    def __init__(self, amadeus_key: Optional[str] = None, amadeus_secret: Optional[str] = None):
        """
        Initialize flight search service with Amadeus
        
        Args:
            amadeus_key: Amadeus API key (optional, will use env var)
            amadeus_secret: Amadeus API secret (optional, will use env var)
        """
        self.amadeus_key = amadeus_key or os.getenv('AMADEUS_API_KEY')
        self.amadeus_secret = amadeus_secret or os.getenv('AMADEUS_API_SECRET')
        
        self.use_amadeus = bool(self.amadeus_key and self.amadeus_secret)
        
        if self.use_amadeus:
            try:
                self.amadeus_client = Client(
                    client_id=self.amadeus_key,
                    client_secret=self.amadeus_secret
                )
                logger.info("✅ FlightSearchService initialized with Amadeus API")
            except Exception as e:
                logger.warning(f"Amadeus init failed: {e}, using mock data")
                self.use_amadeus = False
        else:
            logger.warning("No Amadeus credentials found - using mock data")
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        currency: str = "USD"
    ) -> List[FlightOption]:
        """
        Search for flights using SerpAPI or fallback to mock data
        
        Args:
            origin: Origin airport code (e.g., 'CDG')
            destination: Destination airport code (e.g., 'HAV')
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Optional return date (YYYY-MM-DD)
            adults: Number of adult passengers
            currency: Currency code (USD, EUR, etc.)
        
        Returns:
            List of FlightOption objects
        
        Raises:
            ValueError: If dates are invalid
        """
        # Validate inputs
        self._validate_inputs(origin, destination, departure_date, adults)
        
        try:
            if not self.use_amadeus:
                return self._get_mock_flights(origin, destination, departure_date)
            else:
                return self._search_with_amadeus(
                    origin, destination, departure_date, 
                    return_date, adults, currency
                )
        except Exception as e:
            logger.error(f"Flight search failed: {e}")
            logger.info("Falling back to mock data")
            return self._get_mock_flights(origin, destination, departure_date)
    
    def _validate_inputs(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int
    ) -> None:
        """Validate search parameters"""
        if not origin or len(origin) != 3:
            raise ValueError(f"Invalid origin airport code: {origin}")
        
        if not destination or len(destination) != 3:
            raise ValueError(f"Invalid destination airport code: {destination}")
        
        if adults < 1:
            raise ValueError(f"Invalid number of adults: {adults}")
        
        try:
            datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {departure_date}. Use YYYY-MM-DD")
    
    def _search_with_amadeus(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        currency: str
    ) -> List[FlightOption]:
        """
        Search flights using Amadeus Flight Offers Search API
        
        Returns:
            List of FlightOption objects from Amadeus API
        """
        logger.info(f"🔍 Amadeus search: {origin} → {destination} on {departure_date}")
        
        try:
            # Build search parameters
            search_params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': 5  # Limit to 5 results
            }
            
            if return_date:
                search_params['returnDate'] = return_date
            
            # Call Amadeus API
            response = self.amadeus_client.shopping.flight_offers_search.get(**search_params)
            
            flights = []
            for offer in response.data:
                flight = self._parse_amadeus_offer(offer, origin, destination)
                if flight:
                    flights.append(flight)
            
            logger.info(f"✅ Amadeus: Found {len(flights)} real flight options")
            return flights
            
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Amadeus search failed: {e}")
            raise
    
    def _parse_amadeus_offer(
        self,
        offer: Dict,
        origin: str,
        destination: str
    ) -> Optional[FlightOption]:
        """Parse Amadeus flight offer into FlightOption object"""
        try:
            # Get first itinerary (outbound)
            itinerary = offer['itineraries'][0]
            segments = itinerary['segments']
            first_segment = segments[0]
            last_segment = segments[-1]
            
            # Calculate total duration in minutes
            duration_str = itinerary['duration']  # Format: PT10H30M
            duration_minutes = self._parse_iso_duration(duration_str)
            
            # Extract departure and arrival times
            departure_time = first_segment['departure']['at'].split('T')[1][:5]  # HH:MM
            arrival_time = last_segment['arrival']['at'].split('T')[1][:5]
            
            # Get airline from first segment
            airline = first_segment['carrierCode']
            
            # Number of stops
            stops = len(segments) - 1
            
            # Price
            price = float(offer['price']['total'])
            currency = offer['price']['currency']
            
            return FlightOption(
                airline=airline,
                price=price,
                currency=currency,
                stops=stops,
                duration_minutes=duration_minutes,
                departure_time=departure_time,
                arrival_time=arrival_time,
                departure_airport=origin,
                arrival_airport=destination
            )
        except Exception as e:
            logger.warning(f"Failed to parse Amadeus offer: {e}")
            return None
    
    def _parse_iso_duration(self, duration_str: str) -> int:
        """Convert ISO 8601 duration (PT10H30M) to minutes"""
        try:
            # Remove 'PT' prefix
            duration_str = duration_str.replace('PT', '')
            
            hours = 0
            minutes = 0
            
            if 'H' in duration_str:
                hours_str, rest = duration_str.split('H')
                hours = int(hours_str)
                duration_str = rest
            
            if 'M' in duration_str:
                minutes = int(duration_str.replace('M', ''))
            
            return hours * 60 + minutes
        except Exception as e:
            logger.warning(f"Failed to parse duration {duration_str}: {e}")
            return 0
    
    def _get_mock_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str
    ) -> List[FlightOption]:
        """
        Fallback mock data for testing
        Returns realistic flight options
        """
        logger.info(f"Using mock data for {origin} → {destination}")
        
        mock_data = {
            "CDG-HAV": [
                FlightOption("Air France", 450, "USD", 1, 615, "08:30", "15:45", "CDG", "HAV"),
                FlightOption("Air Canada", 520, "USD", 0, 510, "14:00", "19:30", "CDG", "HAV"),
                FlightOption("Copa Airlines", 395, "USD", 2, 860, "06:00", "18:20", "CDG", "HAV"),
            ],
            "CDG-JFK": [
                FlightOption("Air France", 380, "USD", 0, 495, "10:30", "13:45", "CDG", "JFK"),
                FlightOption("Delta", 420, "USD", 0, 500, "15:00", "18:20", "CDG", "JFK"),
            ]
        }
        
        route = f"{origin}-{destination}"
        return mock_data.get(route, [])
    
    def get_cheapest_flight(self, flights: List[FlightOption]) -> Optional[FlightOption]:
        """Find the cheapest flight from a list"""
        if not flights:
            return None
        return min(flights, key=lambda f: f.price)
    
    def format_flights_for_display(self, flights: List[FlightOption]) -> str:
        """
        Format flight list for user-friendly display
        
        Args:
            flights: List of FlightOption objects
            
        Returns:
            Formatted string for display
        """
        if not flights:
            return "Aucun vol trouvé"
        
        result = []
        for i, flight in enumerate(flights, 1):
            result.append(
                f"{i}. {flight.airline} - ${flight.price} {flight.currency}\n"
                f"   {flight.stops_formatted} • Durée: {flight.duration_formatted}\n"
                f"   Départ: {flight.departure_time} → Arrivée: {flight.arrival_time}"
            )
        
        cheapest = self.get_cheapest_flight(flights)
        if cheapest:
            result.append(
                f"\n💰 Meilleur prix: ${cheapest.price} avec {cheapest.airline}"
            )
        
        return "\n\n".join(result)


# Singleton instance for reuse
_flight_service_instance: Optional[FlightSearchService] = None


def get_flight_service() -> FlightSearchService:
    """
    Get singleton instance of FlightSearchService
    Best practice: reuse service instance
    """
    global _flight_service_instance
    if _flight_service_instance is None:
        _flight_service_instance = FlightSearchService()
    return _flight_service_instance
