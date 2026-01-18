"""
Service de recommandations culturelles (musées, galeries, expositions)
Basé sur les préférences des touristes et les incontournables de la ville
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import requests
from datetime import datetime


@dataclass
class CulturalActivity:
    """Représente une activité culturelle (musée, galerie, monument)"""
    name: str
    type: str  # 'museum', 'gallery', 'monument', 'exhibition', 'theater'
    category: str  # 'art', 'history', 'science', 'architecture', 'performing_arts'
    description: str
    address: str
    latitude: float
    longitude: float
    rating: float
    price_range: str  # 'free', '$', '$$', '$$$', '$$$$'
    opening_hours: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    booking_url: Optional[str] = None
    must_see: bool = False  # Incontournable de la ville
    estimated_duration: Optional[str] = None  # '1-2 hours', '2-3 hours', etc.


class CulturalRecommendationService:
    """Service pour recommander des activités culturelles selon les goûts"""
    
    def __init__(self):
        self.overpass_urls = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
        ]
        
    def find_cultural_activities(
        self,
        city: str,
        latitude: float,
        longitude: float,
        preferences: List[str] = None,
        radius_km: float = 5.0,
        max_results: int = 15
    ) -> List[CulturalActivity]:
        """
        Trouve les activités culturelles selon les préférences
        
        Args:
            city: Ville
            latitude: Latitude du point central
            longitude: Longitude du point central
            preferences: Liste de préférences ['art', 'history', 'science', 'architecture']
            radius_km: Rayon de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste d'activités culturelles triées par pertinence
        """
        if preferences is None:
            preferences = ['art', 'history', 'architecture']
        
        try:
            # Requête Overpass pour musées, galeries, théâtres
            overpass_query = f"""
            [out:json][timeout:25];
            (
              node["tourism"="museum"](around:{radius_km * 1000},{latitude},{longitude});
              node["tourism"="gallery"](around:{radius_km * 1000},{latitude},{longitude});
              node["amenity"="theatre"](around:{radius_km * 1000},{latitude},{longitude});
              node["tourism"="artwork"](around:{radius_km * 1000},{latitude},{longitude});
              way["tourism"="museum"](around:{radius_km * 1000},{latitude},{longitude});
              way["tourism"="gallery"](around:{radius_km * 1000},{latitude},{longitude});
              way["amenity"="theatre"](around:{radius_km * 1000},{latitude},{longitude});
            );
            out center tags {max_results * 3};
            """
            
            # Essayer les serveurs Overpass
            data = None
            for overpass_url in self.overpass_urls:
                try:
                    response = requests.post(overpass_url, data=overpass_query, timeout=20)
                    response.raise_for_status()
                    data = response.json()
                    break
                except:
                    continue
            
            if not data:
                # Fallback sur données mock si API échoue
                return self._get_mock_cultural_activities(city, preferences)
            
            activities = []
            
            for element in data.get('elements', []):
                if 'lat' in element and 'lon' in element:
                    attr_lat = element['lat']
                    attr_lon = element['lon']
                elif 'center' in element:
                    attr_lat = element['center']['lat']
                    attr_lon = element['center']['lon']
                else:
                    continue
                
                tags = element.get('tags', {})
                name = tags.get('name', tags.get('name:en', 'Sans nom'))
                
                if name == 'Sans nom':
                    continue
                
                # Déterminer type et catégorie
                activity_type = tags.get('tourism', tags.get('amenity', 'museum'))
                category = self._determine_category(tags, activity_type)
                
                # Filtrer selon préférences
                if not self._matches_preferences(category, preferences):
                    continue
                
                # Description
                description = tags.get('description', tags.get('description:en', ''))
                
                # Adresse
                addr_parts = []
                if 'addr:housenumber' in tags:
                    addr_parts.append(tags['addr:housenumber'])
                if 'addr:street' in tags:
                    addr_parts.append(tags['addr:street'])
                address = ' '.join(addr_parts) if addr_parts else f"{city}"
                
                # Distance
                distance = self._calculate_distance(latitude, longitude, attr_lat, attr_lon)
                
                # Website
                website = tags.get('website', tags.get('contact:website'))
                phone = tags.get('phone', tags.get('contact:phone'))
                
                # Horaires
                opening_hours = tags.get('opening_hours', 'Non disponible')
                
                # Prix (estimation basée sur tags)
                price_range = self._estimate_price(tags)
                
                activities.append(CulturalActivity(
                    name=name,
                    type=activity_type,
                    category=category,
                    description=description or f"{activity_type.capitalize()} à {city}",
                    address=address,
                    latitude=attr_lat,
                    longitude=attr_lon,
                    rating=4.0,  # Default, serait mieux avec Yelp/Google
                    price_range=price_range,
                    opening_hours=opening_hours,
                    website=website,
                    phone=phone,
                    must_see=tags.get('heritage') is not None or 'unesco' in name.lower(),
                    estimated_duration='2-3 hours'
                ))
            
            # Trier par pertinence (must_see d'abord, puis distance)
            activities.sort(key=lambda x: (not x.must_see, self._calculate_distance(
                latitude, longitude, x.latitude, x.longitude
            )))
            
            return activities[:max_results]
            
        except Exception as e:
            print(f"❌ Error finding cultural activities: {e}")
            return self._get_mock_cultural_activities(city, preferences)
    
    def _determine_category(self, tags: Dict, activity_type: str) -> str:
        """Détermine la catégorie d'une activité"""
        museum_type = tags.get('museum', '').lower()
        
        if 'art' in museum_type or activity_type == 'gallery':
            return 'art'
        elif 'history' in museum_type or 'archaeological' in museum_type:
            return 'history'
        elif 'science' in museum_type or 'technology' in museum_type:
            return 'science'
        elif activity_type == 'theatre':
            return 'performing_arts'
        else:
            return 'architecture'
    
    def _matches_preferences(self, category: str, preferences: List[str]) -> bool:
        """Vérifie si une catégorie correspond aux préférences"""
        if not preferences:
            return True
        return category in preferences
    
    def _estimate_price(self, tags: Dict) -> str:
        """Estime le prix d'entrée"""
        fee = tags.get('fee', '')
        charge = tags.get('charge', '')
        
        if fee == 'no' or 'free' in charge.lower():
            return 'free'
        elif fee == 'yes':
            return '$$'  # Prix moyen par défaut
        else:
            return '$'
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance entre deux points GPS"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def _get_mock_cultural_activities(self, city: str, preferences: List[str]) -> List[CulturalActivity]:
        """Données mock pour fallback"""
        mock_data = {
            "Havana": [
                CulturalActivity(
                    name="Museo Nacional de Bellas Artes",
                    type="museum",
                    category="art",
                    description="Plus important musée d'art de Cuba avec collection d'art cubain et universel",
                    address="Trocadero e/ Zulueta y Monserrate",
                    latitude=23.1373,
                    longitude=-82.3560,
                    rating=4.5,
                    price_range="$",
                    opening_hours="9h-17h (fermé lundi)",
                    website="https://www.bellasartes.co.cu",
                    must_see=True,
                    estimated_duration="2-3 hours"
                ),
                CulturalActivity(
                    name="Museo de la Revolución",
                    type="museum",
                    category="history",
                    description="Histoire de la révolution cubaine dans l'ancien palais présidentiel",
                    address="Refugio 1, La Habana",
                    latitude=23.1394,
                    longitude=-82.3605,
                    rating=4.3,
                    price_range="$",
                    opening_hours="10h-17h",
                    must_see=True,
                    estimated_duration="2-3 hours"
                ),
                CulturalActivity(
                    name="Gran Teatro de La Habana",
                    type="theater",
                    category="performing_arts",
                    description="Magnifique théâtre néo-baroque, siège du Ballet National de Cuba",
                    address="Paseo de Martí 458",
                    latitude=23.1356,
                    longitude=-82.3598,
                    rating=4.7,
                    price_range="$$",
                    opening_hours="Selon spectacles",
                    website="https://www.balletcuba.cu",
                    must_see=True,
                    estimated_duration="3 hours"
                ),
            ],
            "New York": [
                CulturalActivity(
                    name="The Metropolitan Museum of Art",
                    type="museum",
                    category="art",
                    description="Un des plus grands musées d'art au monde",
                    address="1000 5th Ave, New York",
                    latitude=40.7794,
                    longitude=-73.9632,
                    rating=4.8,
                    price_range="$$$",
                    opening_hours="10h-17h",
                    website="https://www.metmuseum.org",
                    must_see=True,
                    estimated_duration="3-4 hours"
                ),
                CulturalActivity(
                    name="American Museum of Natural History",
                    type="museum",
                    category="science",
                    description="Musée de sciences naturelles et d'histoire naturelle",
                    address="Central Park West, New York",
                    latitude=40.7813,
                    longitude=-73.9740,
                    rating=4.7,
                    price_range="$$",
                    opening_hours="10h-17h45",
                    website="https://www.amnh.org",
                    must_see=True,
                    estimated_duration="3-4 hours"
                ),
            ]
        }
        
        activities = mock_data.get(city, [])
        
        # Filtrer selon préférences
        if preferences:
            activities = [a for a in activities if a.category in preferences]
        
        return activities
    
    def format_activities_for_display(self, activities: List[CulturalActivity]) -> str:
        """Formate les activités pour affichage"""
        if not activities:
            return "Aucune activité trouvée"
        
        result = ""
        
        # Grouper par catégorie
        by_category = {}
        for activity in activities:
            if activity.category not in by_category:
                by_category[activity.category] = []
            by_category[activity.category].append(activity)
        
        category_icons = {
            'art': '🎨',
            'history': '🏛️',
            'science': '🔬',
            'architecture': '🏰',
            'performing_arts': '🎭'
        }
        
        for category, acts in sorted(by_category.items()):
            icon = category_icons.get(category, '📍')
            result += f"\n{icon} {category.upper().replace('_', ' ')}:\n\n"
            
            for i, act in enumerate(acts, 1):
                must_see = "⭐ INCONTOURNABLE" if act.must_see else ""
                result += f"{i}. {act.name} {must_see}\n"
                result += f"   {act.description}\n"
                result += f"   📍 {act.address}\n"
                result += f"   💰 {act.price_range} | ⏱️ {act.estimated_duration}\n"
                result += f"   ⭐ {act.rating}/5 | 🕐 {act.opening_hours}\n"
                
                if act.website:
                    result += f"   🔗 {act.website}\n"
                if act.booking_url:
                    result += f"   🎫 Réserver: {act.booking_url}\n"
                
                result += "\n"
        
        return result


# Singleton
_cultural_service_instance: Optional[CulturalRecommendationService] = None


def get_cultural_service() -> CulturalRecommendationService:
    """Retourne l'instance singleton"""
    global _cultural_service_instance
    if _cultural_service_instance is None:
        _cultural_service_instance = CulturalRecommendationService()
    return _cultural_service_instance
