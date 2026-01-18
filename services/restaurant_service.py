"""
Service de recommandations de restaurants
Utilise Travel Advisor API (RapidAPI) pour de vraies données
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class Restaurant:
    """Représente un restaurant recommandé"""
    name: str
    cuisine_type: str  # 'local', 'french', 'italian', 'asian', 'american', etc.
    description: str
    address: str
    latitude: float
    longitude: float
    rating: float
    price_range: str  # '$', '$$', '$$$', '$$$$'
    specialties: List[str]
    atmosphere: str  # 'casual', 'fine_dining', 'romantic', 'family_friendly'
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    reservation_url: Optional[str] = None
    distance_km: float = 0.0
    num_reviews: int = 0
    photo_url: Optional[str] = None


class RestaurantRecommendationService:
    """Service pour recommander des restaurants via Travel Advisor API + Foursquare fallback"""
    
    def __init__(self):
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.rapidapi_host = "travel-advisor.p.rapidapi.com"
        self.foursquare_api_key = os.getenv("FOURSQUARE_API_KEY")
        self.headers_rapidapi = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }
        # Fallback Overpass
        self.overpass_urls = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
        ]
    
    def find_restaurants(
        self,
        city: str,
        latitude: float,
        longitude: float,
        cuisine_preferences: List[str] = None,
        budget: str = '$$',
        atmosphere: str = None,
        radius_km: float = 3.0,
        max_results: int = 10
    ) -> List[Restaurant]:
        """
        Trouve des restaurants via Travel Advisor API → Yelp → Overpass
        
        Args:
            city: Ville
            latitude: Latitude du point central (hôtel)
            longitude: Longitude du point central
            cuisine_preferences: Types de cuisine ['local', 'french', 'italian', 'asian']
            budget: Budget '$' à '$$$$'
            atmosphere: Ambiance souhaitée
            radius_km: Rayon de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de restaurants triés par pertinence
        """
        if cuisine_preferences is None:
            cuisine_preferences = ['local']
        
        # Tentative 1: Travel Advisor API (RapidAPI)
        restaurants = self._try_travel_advisor_api(city, latitude, longitude, cuisine_preferences, budget, radius_km, max_results)
        
        if restaurants:
            logger.info(f"✅ {len(restaurants)} restaurants from Travel Advisor API")
            return restaurants
        
        # Tentative 2: Foursquare Places API
        logger.warning("Travel Advisor failed, trying Foursquare Places API...")
        restaurants = self._try_foursquare_api(latitude, longitude, cuisine_preferences, budget, radius_km, max_results)
        
        if restaurants:
            logger.info(f"✅ {len(restaurants)} restaurants from Foursquare API")
            return restaurants
        
        # Tentative 3: OpenStreetMap Overpass API
        logger.warning("Yelp failed, trying Overpass API...")
        restaurants = self._try_overpass_api(city, latitude, longitude, cuisine_preferences, budget, radius_km, max_results)
        
        if restaurants:
            logger.info(f"✅ {len(restaurants)} restaurants from Overpass API")
            return restaurants
        
        # Si tout échoue, retourner message d'erreur
        logger.error("All restaurant APIs failed")
        return [Restaurant(
            name="Aucune API disponible",
            cuisine_type="N/A",
            description="Les APIs de restaurants sont temporairement indisponibles. Veuillez réessayer plus tard.",
            address=city,
            latitude=latitude,
            longitude=longitude,
            rating=0.0,
            price_range=budget,
            specialties=[],
            atmosphere="N/A"
        )]
    
    def _try_travel_advisor_api(self, city: str, latitude: float, longitude: float, 
                                cuisine_preferences: List[str], budget: str, 
                                radius_km: float, max_results: int) -> List[Restaurant]:
        """Tentative avec Travel Advisor API"""
        try:
            url = "https://travel-advisor.p.rapidapi.com/restaurants/list-by-latlng"
            
            querystring = {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "limit": str(max_results * 2),
                "distance": str(int(radius_km)),
                "currency": "USD",
                "lang": "fr_FR"
            }
            
            response = requests.get(url, headers=self.headers_rapidapi, params=querystring, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                return []
            
            restaurants = []
            
            for item in data.get('data', [])[:max_results * 2]:
                try:
                    name = item.get('name')
                    if not name:
                        continue
                    
                    rest_lat = float(item.get('latitude', latitude))
                    rest_lon = float(item.get('longitude', longitude))
                    rating = float(item.get('rating', 4.0))
                    
                    price_level = item.get('price_level', '$$')
                    if not price_level.startswith('$'):
                        price_map = {'PRICE_LEVEL_INEXPENSIVE': '$', 'PRICE_LEVEL_MODERATE': '$$', 
                                    'PRICE_LEVEL_EXPENSIVE': '$$$', 'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$'}
                        price_level = price_map.get(price_level, '$$')
                    
                    if not self._matches_budget(price_level, budget):
                        continue
                    
                    cuisine_types = item.get('cuisine', [])
                    if isinstance(cuisine_types, list) and cuisine_types:
                        cuisine = cuisine_types[0].get('name', 'local').lower()
                    else:
                        cuisine = 'local'
                    
                    if not self._matches_cuisine_preferences(cuisine, cuisine_preferences):
                        continue
                    
                    address = item.get('address', f"{city}")
                    description = item.get('description', f"Restaurant {cuisine} à {city}")
                    specialties = [c.get('name', '') for c in cuisine_types[:3]] if isinstance(cuisine_types, list) else []
                    phone = item.get('phone')
                    website = item.get('website')
                    
                    photo_url = None
                    if item.get('photo'):
                        images = item['photo'].get('images')
                        if images and isinstance(images, dict):
                            photo_url = images.get('medium', {}).get('url') or images.get('large', {}).get('url')
                    
                    num_reviews = int(item.get('num_reviews', 0))
                    distance_km = float(item.get('distance', 0))
                    
                    restaurant = Restaurant(
                        name=name,
                        cuisine_type=cuisine,
                        description=description[:200],
                        address=address,
                        latitude=rest_lat,
                        longitude=rest_lon,
                        rating=rating,
                        price_range=price_level,
                        specialties=specialties,
                        atmosphere='casual',
                        phone=phone,
                        website=website,
                        reservation_url=website,
                        distance_km=distance_km,
                        num_reviews=num_reviews,
                        photo_url=photo_url
                    )
                    restaurants.append(restaurant)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Travel Advisor restaurant: {e}")
                    continue
            
            restaurants.sort(key=lambda r: (r.rating, r.num_reviews), reverse=True)
            return restaurants[:max_results]
            
        except Exception as e:
            logger.error(f"Travel Advisor API error: {e}")
            return []
    
    def _try_foursquare_api(self, latitude: float, longitude: float, 
                           cuisine_preferences: List[str], budget: str, 
                           radius_km: float, max_results: int) -> List[Restaurant]:
        """Tentative avec Foursquare Places API (100% gratuit)"""
        if not self.foursquare_api_key or self.foursquare_api_key == "your_foursquare_api_key_here":
            logger.warning("Foursquare API key not configured")
            return []
        
        try:
            # Foursquare Places API v3
            url = "https://api.foursquare.com/v3/places/search"
            
            headers = {
                "Authorization": self.foursquare_api_key,
                "accept": "application/json"
            }
            
            # Mapper les préférences cuisine vers les catégories Foursquare
            categories = self._map_cuisine_to_foursquare_categories(cuisine_preferences)
            
            params = {
                "ll": f"{latitude},{longitude}",
                "radius": int(radius_km * 1000),  # Foursquare utilise des mètres
                "categories": categories,
                "limit": max_results,
                "fields": "name,location,rating,price,photos,tel,website,hours,distance,categories"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('results'):
                return []
            
            restaurants = []
            
            for item in data.get('results', []):
                try:
                    name = item.get('name')
                    if not name:
                        continue
                    
                    geocodes = item.get('geocodes', {}).get('main', {})
                    rest_lat = geocodes.get('latitude', latitude)
                    rest_lon = geocodes.get('longitude', longitude)
                    
                    rating = float(item.get('rating', 4.0) / 2)  # Foursquare: 0-10, nous: 0-5
                    
                    # Prix Foursquare: 1-4
                    price_tier = item.get('price', 2)
                    price_level = '$' * price_tier if price_tier else '$$'
                    
                    if not self._matches_budget(price_level, budget):
                        continue
                    
                    categories_list = item.get('categories', [])
                    cuisine = categories_list[0].get('name', 'Restaurant') if categories_list else 'Restaurant'
                    
                    location = item.get('location', {})
                    address_parts = [
                        location.get('address'),
                        location.get('locality'),
                        location.get('region')
                    ]
                    address = ', '.join([p for p in address_parts if p]) or 'Address not available'
                    
                    phone = item.get('tel')
                    website = item.get('website')
                    
                    # Photos
                    photo_url = None
                    photos = item.get('photos', [])
                    if photos:
                        photo = photos[0]
                        prefix = photo.get('prefix')
                        suffix = photo.get('suffix')
                        if prefix and suffix:
                            photo_url = f"{prefix}300x300{suffix}"
                    
                    distance_km = item.get('distance', 0) / 1000
                    
                    specialties = [cat.get('name') for cat in categories_list[:3]]
                    
                    # Hours
                    hours_data = item.get('hours', {})
                    opening_hours = "Voir le site" if hours_data else "Non disponible"
                    
                    restaurant = Restaurant(
                        name=name,
                        cuisine_type=cuisine.lower(),
                        description=f"Restaurant recommandé par Foursquare - {rating:.1f}⭐",
                        address=address,
                        latitude=rest_lat,
                        longitude=rest_lon,
                        rating=rating,
                        price_range=price_level,
                        specialties=specialties,
                        atmosphere='casual',
                        opening_hours=opening_hours,
                        phone=phone,
                        website=website,
                        reservation_url=website,
                        distance_km=round(distance_km, 2),
                        num_reviews=0,
                        photo_url=photo_url
                    )
                    restaurants.append(restaurant)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Foursquare restaurant: {e}")
                    continue
            
            restaurants.sort(key=lambda r: r.rating, reverse=True)
            return restaurants[:max_results]
            
        except Exception as e:
            logger.error(f"Foursquare API error: {e}")
            return []
    
    def _map_cuisine_to_foursquare_categories(self, cuisine_preferences: List[str]) -> str:
        """Mappe les préférences vers les catégories Foursquare"""
        # Foursquare category IDs pour restaurants
        mapping = {
            'local': '13065',  # Restaurant
            'french': '13148',  # French Restaurant
            'italian': '13236',  # Italian Restaurant
            'asian': '13099',  # Asian Restaurant
            'chinese': '13145',  # Chinese Restaurant
            'japanese': '13263',  # Japanese Restaurant
            'american': '13064',  # American Restaurant
            'fusion': '13199'  # Fusion Restaurant
        }
        
        categories = []
        for pref in cuisine_preferences:
            if pref.lower() in mapping:
                categories.append(mapping[pref.lower()])
        
        return ','.join(categories) if categories else '13065'  # Default: Restaurant
    def _try_overpass_api(self, city: str, latitude: float, longitude: float, 
                         cuisine_preferences: List[str], budget: str, 
                         radius_km: float, max_results: int) -> List[Restaurant]:
        """Tentative avec Overpass API (OpenStreetMap)"""
        try:
            overpass_query = f"""
            [out:json][timeout:20];
            (
              node["amenity"="restaurant"](around:{radius_km * 1000},{latitude},{longitude});
              way["amenity"="restaurant"](around:{radius_km * 1000},{latitude},{longitude});
            );
            out center tags {max_results * 3};
            """
            
            data = None
            for overpass_url in self.overpass_urls:
                try:
                    response = requests.post(overpass_url, data=overpass_query, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    break
                except:
                    continue
            
            if not data or not data.get('elements'):
                return []
            
            restaurants = []
            
            for element in data.get('elements', []):
                if 'lat' in element and 'lon' in element:
                    rest_lat = element['lat']
                    rest_lon = element['lon']
                elif 'center' in element:
                    rest_lat = element['center']['lat']
                    rest_lon = element['center']['lon']
                else:
                    continue
                
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en'))
                
                if not name or name == 'Sans nom':
                    continue
                
                cuisine = tags.get('cuisine', 'local').split(';')[0]
                
                if not self._matches_cuisine_preferences(cuisine, cuisine_preferences):
                    continue
                
                description = f"Restaurant {cuisine} trouvé sur OpenStreetMap"
                
                addr_parts = []
                if 'addr:housenumber' in tags:
                    addr_parts.append(tags['addr:housenumber'])
                if 'addr:street' in tags:
                    addr_parts.append(tags['addr:street'])
                address = ' '.join(addr_parts) if addr_parts else f"{city}"
                
                price_level = self._estimate_price_from_tags(tags)
                distance = self._calculate_distance(latitude, longitude, rest_lat, rest_lon)
                
                restaurant = Restaurant(
                    name=name,
                    cuisine_type=cuisine,
                    description=description,
                    address=address,
                    latitude=rest_lat,
                    longitude=rest_lon,
                    rating=4.0,
                    price_range=price_level,
                    specialties=[cuisine],
                    atmosphere=self._determine_atmosphere(tags),
                    opening_hours=tags.get('opening_hours', 'Non disponible'),
                    phone=tags.get('phone', tags.get('contact:phone')),
                    website=tags.get('website', tags.get('contact:website')),
                    distance_km=round(distance, 2)
                )
                restaurants.append(restaurant)
            
            restaurants = [r for r in restaurants if self._matches_budget(r.price_range, budget)]
            restaurants.sort(key=lambda x: x.distance_km)
            
            return restaurants[:max_results]
            
        except Exception as e:
            logger.error(f"Overpass API error: {e}")
            return []
    
    def _map_cuisine_to_yelp_categories(self, cuisine_preferences: List[str]) -> str:
        """Mappe les préférences vers les catégories Yelp"""
        mapping = {
            'local': 'restaurants',
            'french': 'french',
            'italian': 'italian',
            'asian': 'asian',
            'chinese': 'chinese',
            'japanese': 'japanese',
            'american': 'newamerican',
            'fusion': 'fusion'
        }
        
        categories = []
        for pref in cuisine_preferences:
            if pref.lower() in mapping:
                categories.append(mapping[pref.lower()])
        
        return ','.join(categories) if categories else 'restaurants'
    
    def _matches_cuisine_preferences(self, cuisine: str, preferences: List[str]) -> bool:
        """Vérifie si un type de cuisine correspond aux préférences"""
        if not preferences or 'any' in preferences:
            return True
        
        cuisine_lower = cuisine.lower()
        for pref in preferences:
            if pref.lower() in cuisine_lower or cuisine_lower in pref.lower():
                return True
        
        return False
    
    def _matches_budget(self, price_range: str, budget: str) -> bool:
        """Vérifie si le prix correspond au budget"""
        price_levels = {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}
        return price_levels.get(price_range, 2) <= price_levels.get(budget, 2)
    
    def _estimate_price_from_tags(self, tags: Dict) -> str:
        """Estime le niveau de prix"""
        # Logique simple, pourrait être améliorée avec Yelp/Google
        if 'fine_dining' in tags.get('cuisine', ''):
            return '$$$'
        elif 'fast_food' in tags.get('cuisine', ''):
            return '$'
        else:
            return '$$'
    
    def _determine_atmosphere(self, tags: Dict) -> str:
        """Détermine l'ambiance"""
        if tags.get('outdoor_seating') == 'yes':
            return 'casual'
        elif 'fine_dining' in tags.get('cuisine', ''):
            return 'fine_dining'
        else:
            return 'family_friendly'
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance entre deux points"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def format_restaurants_for_display(self, restaurants: List[Restaurant]) -> str:
        """Formate les restaurants pour affichage"""
        if not restaurants:
            return "Aucun restaurant trouvé"
        
        result = ""
        
        for i, resto in enumerate(restaurants, 1):
            result += f"\n{i}. {resto.name} - {resto.rating}⭐\n"
            result += f"   🍽️ Cuisine: {resto.cuisine_type}\n"
            result += f"   {resto.description}\n"
            result += f"   📍 {resto.address} ({resto.distance_km} km)\n"
            result += f"   💰 {resto.price_range} | 🕐 {resto.opening_hours}\n"
            
            if resto.specialties:
                result += f"   ⭐ Spécialités: {', '.join(resto.specialties[:3])}\n"
            
            if resto.phone:
                result += f"   📞 {resto.phone}\n"
            
            if resto.website:
                result += f"   🔗 {resto.website}\n"
            
            if resto.reservation_url:
                result += f"   🎫 Réserver: {resto.reservation_url}\n"
            
            result += "\n"
        
        return result


# Singleton
_restaurant_service_instance: Optional[RestaurantRecommendationService] = None


def get_restaurant_service() -> RestaurantRecommendationService:
    """Retourne l'instance singleton"""
    global _restaurant_service_instance
    if _restaurant_service_instance is None:
        _restaurant_service_instance = RestaurantRecommendationService()
    return _restaurant_service_instance
