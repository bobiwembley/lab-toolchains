"""
Service de géolocalisation et recherche de lieux d'intérêt.

Utilise:
- Nominatim (OpenStreetMap) pour le geocoding
- Overpass API pour les POI (Points of Interest)
- Folium pour la génération de cartes
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import requests
import time
from datetime import datetime


@dataclass
class Location:
    """Représente une localisation géographique"""
    name: str
    address: str
    latitude: float
    longitude: float
    type: str  # 'hotel', 'attraction', 'rental'


@dataclass
class Attraction:
    """Représente un lieu d'intérêt touristique"""
    name: str
    type: str  # 'monument', 'museum', 'church', 'castle', etc.
    latitude: float
    longitude: float
    distance_km: float
    description: Optional[str] = None
    address: Optional[str] = None
    wikipedia_url: Optional[str] = None


class LocationService:
    """Service pour géolocaliser et trouver des attractions"""
    
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        # Serveurs Overpass alternatifs (avec fallback)
        self.overpass_urls = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
            "https://overpass.osm.ch/api/interpreter"
        ]
        self.user_agent = "TravelAgent/1.0"
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Nominatim: 1 req/sec max
    
    def _rate_limit(self):
        """Respect Nominatim rate limit (1 request per second)"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def geocode_address(self, address: str, city: str = "") -> Optional[Location]:
        """
        Convertit une adresse en coordonnées GPS
        
        Args:
            address: Adresse ou nom de ville à géolocaliser
            city: Ville (optionnel, peut être vide si address contient déjà la ville)
            
        Returns:
            Location ou None si non trouvé
        """
        try:
            self._rate_limit()
            
            # Si city est vide, chercher directement l'adresse
            query = f"{address}, {city}".strip(', ') if city else address
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 5,  # Plusieurs résultats pour validation
                'addressdetails': 1
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(
                f"{self.nominatim_url}/search",
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            if not results:
                print(f"❌ No results for: {query}")
                return None
            
            # Prendre le premier résultat et logger
            result = results[0]
            display_name = result.get('display_name', query)
            print(f"🗺️ Geocoded '{query}' → {display_name}")
            
            # Vérifier que le résultat correspond à la ville demandée
            if city and city.lower() not in display_name.lower():
                print(f"⚠️  Warning: Result doesn't match requested city '{city}'")
            
            return Location(
                name=query,
                address=display_name,
                latitude=float(result['lat']),
                longitude=float(result['lon']),
                type='unknown'
            )
            
        except Exception as e:
            print(f"❌ Geocoding error for {query}: {e}")
            return None
    
    def find_nearby_attractions(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 3.0,
        max_results: int = 15
    ) -> List[Attraction]:
        """
        Trouve les attractions historiques autour d'un point
        
        Args:
            latitude: Latitude du point central
            longitude: Longitude du point central
            radius_km: Rayon de recherche en km
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste d'attractions triées par distance
        """
        try:
            # Overpass Query Language pour trouver les POI historiques
            # tourism=* : attractions touristiques
            # historic=* : sites historiques
            overpass_query = f"""
            [out:json][timeout:25];
            (
              node["tourism"~"attraction|museum|monument|artwork|gallery|viewpoint"]
                (around:{radius_km * 1000},{latitude},{longitude});
              node["historic"~"monument|memorial|castle|fort|ruins|archaeological_site|battlefield"]
                (around:{radius_km * 1000},{latitude},{longitude});
              way["tourism"~"attraction|museum|monument|artwork|gallery"]
                (around:{radius_km * 1000},{latitude},{longitude});
              way["historic"~"monument|memorial|castle|fort|ruins|archaeological_site|cathedral|church"]
                (around:{radius_km * 1000},{latitude},{longitude});
            );
            out center tags {max_results * 2};
            """
            
            # Essayer les serveurs Overpass avec fallback
            last_error = None
            for overpass_url in self.overpass_urls:
                try:
                    print(f"🔍 Trying Overpass server: {overpass_url}")
                    response = requests.post(
                        overpass_url,
                        data=overpass_query,
                        timeout=20
                    )
                    response.raise_for_status()
                    data = response.json()
                    print(f"✅ Success with {overpass_url}")
                    break  # Success, sortir de la boucle
                except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
                    last_error = e
                    print(f"❌ Failed with {overpass_url}: {e}")
                    continue  # Essayer le serveur suivant
            else:
                # Tous les serveurs ont échoué
                raise Exception(f"All Overpass servers failed. Last error: {last_error}")
            
            attractions = []
            
            for element in data.get('elements', []):
                # Récupérer les coordonnées (node ou center pour way/relation)
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
                
                # Ignorer les éléments sans nom
                if name == 'Sans nom':
                    continue
                
                # Déterminer le type
                attr_type = tags.get('historic', tags.get('tourism', 'attraction'))
                
                # Calculer la distance
                distance = self._calculate_distance(
                    latitude, longitude,
                    attr_lat, attr_lon
                )
                
                # Description
                description = tags.get('description', tags.get('description:en'))
                
                # Wikipedia
                wikipedia_url = None
                if 'wikipedia' in tags:
                    wiki = tags['wikipedia']
                    if ':' in wiki:
                        lang, title = wiki.split(':', 1)
                        wikipedia_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                
                # Adresse
                addr_parts = []
                if 'addr:street' in tags:
                    addr_parts.append(tags['addr:street'])
                if 'addr:housenumber' in tags:
                    addr_parts.insert(0, tags['addr:housenumber'])
                address = ' '.join(addr_parts) if addr_parts else None
                
                attractions.append(Attraction(
                    name=name,
                    type=attr_type,
                    latitude=attr_lat,
                    longitude=attr_lon,
                    distance_km=round(distance, 2),
                    description=description,
                    address=address,
                    wikipedia_url=wikipedia_url
                ))
            
            # Trier par distance et limiter
            attractions.sort(key=lambda x: x.distance_km)
            return attractions[:max_results]
            
        except Exception as e:
            print(f"❌ Error finding attractions: {e}")
            return []
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calcule la distance entre deux points GPS (formule de Haversine)
        
        Returns:
            Distance en kilomètres
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Rayon de la Terre en km
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = (sin(delta_lat / 2) ** 2 +
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def generate_map(
        self,
        locations: List[Location],
        attractions: List[Attraction],
        output_file: str = "travel_map.html"
    ) -> str:
        """
        Génère une carte interactive HTML avec folium
        
        Args:
            locations: Liste des hôtels/locations
            attractions: Liste des attractions
            output_file: Nom du fichier HTML
            
        Returns:
            Chemin du fichier généré
        """
        try:
            import folium
            from folium import Icon, Marker, Circle
            
            # Calculer le centre de la carte
            all_lats = [loc.latitude for loc in locations] + [attr.latitude for attr in attractions]
            all_lons = [loc.longitude for loc in locations] + [attr.longitude for attr in attractions]
            
            center_lat = sum(all_lats) / len(all_lats)
            center_lon = sum(all_lons) / len(all_lons)
            
            # Créer la carte
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles='OpenStreetMap'
            )
            
            # Ajouter les hôtels/locations (marqueurs bleus)
            for loc in locations:
                icon_color = 'blue' if loc.type == 'hotel' else 'green'
                icon = 'home' if loc.type == 'rental' else 'bed'
                
                popup_html = f"""
                <div style='width: 200px'>
                    <h4>{loc.name}</h4>
                    <p><strong>Type:</strong> {loc.type}</p>
                    <p><strong>Adresse:</strong> {loc.address}</p>
                </div>
                """
                
                Marker(
                    location=[loc.latitude, loc.longitude],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=loc.name,
                    icon=Icon(color=icon_color, icon=icon, prefix='fa')
                ).add_to(m)
            
            # Ajouter les attractions (marqueurs rouges)
            for attr in attractions:
                icon_map = {
                    'museum': 'university',
                    'monument': 'monument',
                    'castle': 'fort-awesome',
                    'church': 'church',
                    'memorial': 'monument',
                    'attraction': 'star'
                }
                icon = icon_map.get(attr.type, 'info-circle')
                
                popup_html = f"""
                <div style='width: 250px'>
                    <h4>{attr.name}</h4>
                    <p><strong>Type:</strong> {attr.type}</p>
                    <p><strong>Distance:</strong> {attr.distance_km} km</p>
                """
                
                if attr.description:
                    popup_html += f"<p><strong>Description:</strong> {attr.description[:100]}...</p>"
                
                if attr.address:
                    popup_html += f"<p><strong>Adresse:</strong> {attr.address}</p>"
                
                if attr.wikipedia_url:
                    popup_html += f"<p><a href='{attr.wikipedia_url}' target='_blank'>Wikipedia →</a></p>"
                
                popup_html += "</div>"
                
                Marker(
                    location=[attr.latitude, attr.longitude],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=f"{attr.name} ({attr.distance_km} km)",
                    icon=Icon(color='red', icon=icon, prefix='fa')
                ).add_to(m)
            
            # Ajouter une légende
            legend_html = """
            <div style="position: fixed; 
                        bottom: 50px; right: 50px; width: 200px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
                <p><strong>Légende</strong></p>
                <p><i class="fa fa-bed" style="color:blue"></i> Hôtels</p>
                <p><i class="fa fa-home" style="color:green"></i> Locations</p>
                <p><i class="fa fa-star" style="color:red"></i> Attractions</p>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Sauvegarder
            m.save(output_file)
            return output_file
            
        except ImportError:
            print("❌ folium n'est pas installé. Installez-le avec: pip install folium")
            return ""
        except Exception as e:
            print(f"❌ Error generating map: {e}")
            return ""


# Singleton instance
_location_service_instance: Optional[LocationService] = None


def get_location_service() -> LocationService:
    """Retourne l'instance singleton du service de localisation"""
    global _location_service_instance
    if _location_service_instance is None:
        _location_service_instance = LocationService()
    return _location_service_instance
