"""
Travel-related LangChain tools
Modular tool definitions following LangChain best practices
"""

import logging
import time
from langchain_core.tools import tool
from datetime import datetime
from utils.telemetry import get_telemetry

from services.flight_service import get_flight_service
from services.rental_service import get_rental_service
from services.location_service import get_location_service
from services.cultural_service import get_cultural_service
from services.restaurant_service import get_restaurant_service
from services.wikipedia_service import get_wikipedia_service
from services.airport_service import get_airport_service

logger = logging.getLogger(__name__)


@tool
def get_airport_code(city_name: str) -> str:
    """Trouve le code aéroport IATA (3 lettres) pour une ville donnée.
    
    Args:
        city_name: Nom de la ville (ex: "Rio de Janeiro", "Tokyo", "Paris")
    
    Returns:
        Code IATA et informations sur l'aéroport
        
    Exemples:
        - get_airport_code("Rio de Janeiro") → "GIG (Galeão International Airport)"
        - get_airport_code("Tokyo") → "NRT (Narita International Airport)"
    """
    telemetry = get_telemetry()
    start_time = time.time()
    
    # Créer un span pour l'exécution du tool
    if telemetry:
        tool_span = telemetry.trace_tool_call("get_airport_code")
        span = tool_span.__enter__()
        span.set_attribute("tool.city_name", city_name)
    
    try:
        service = get_airport_service()
        result = service.get_airport_code(city_name)
        
        if not result:
            if telemetry:
                span.set_attribute("tool.result", "not_found")
                tool_span.__exit__(None, None, None)
            return f"❌ Code aéroport introuvable pour '{city_name}'. Essaie avec le nom en anglais ou une ville voisine."
        
        # Enregistrer les métriques de succès
        if telemetry:
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("tool.airport_code", result['code'])
            span.set_attribute("tool.latency_ms", latency_ms)
            span.set_attribute("tool.success", True)
            tool_span.__exit__(None, None, None)
            telemetry.record_tool_call("get_airport_code", latency_ms, True)
        
        return f"✈️ {result['code']} - {result['name']} ({result['city']}, {result['country']})"
        
    except Exception as e:
        # Enregistrer l'erreur dans le span
        if telemetry:
            span.record_exception(e)
            span.set_attribute("tool.success", False)
            tool_span.__exit__(type(e), e, e.__traceback__)
            telemetry.record_error(type(e).__name__, "tool.get_airport_code")
        
        logger.error(f"Error in get_airport_code tool: {e}")
        return f"❌ Erreur: {str(e)}"


@tool
def search_flights(origin: str, destination: str, departure_date: str, return_date: str = None) -> str:
    """Recherche des vols avec prix réels via SerpAPI (ou données mock en fallback).
    
    Args:
        origin: Code aéroport d'origine (ex: 'CDG')
        destination: Code aéroport de destination (ex: 'HAV')
        departure_date: Date de départ format YYYY-MM-DD
        return_date: Date de retour optionnelle format YYYY-MM-DD
    
    Returns:
        Liste formatée des vols avec prix
    """
    telemetry = get_telemetry()
    start_time = time.time()
    
    # Créer un span pour l'exécution du tool
    if telemetry:
        tool_span = telemetry.trace_tool_call("search_flights")
        span = tool_span.__enter__()
        span.set_attribute("tool.origin", origin)
        span.set_attribute("tool.destination", destination)
        span.set_attribute("tool.departure_date", departure_date)
        if return_date:
            span.set_attribute("tool.return_date", return_date)
    
    try:
        service = get_flight_service()
        flights = service.search_flights(origin, destination, departure_date, return_date)
        
        if not flights:
            if telemetry:
                span.set_attribute("tool.result_count", 0)
                span.set_attribute("tool.success", False)
                tool_span.__exit__(None, None, None)
            return f"❌ Aucun vol trouvé pour {origin} → {destination}"
        
        result = f"✈️ Vols {origin} → {destination} ({departure_date}):\n\n"
        result += service.format_flights_for_display(flights)
        
        # Enregistrer les métriques de succès
        if telemetry:
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("tool.result_count", len(flights))
            span.set_attribute("tool.latency_ms", latency_ms)
            span.set_attribute("tool.success", True)
            tool_span.__exit__(None, None, None)
            telemetry.record_tool_call("search_flights", latency_ms, True)
        
        return result
        
    except Exception as e:
        # Enregistrer l'erreur dans le span
        if telemetry:
            span.record_exception(e)
            span.set_attribute("tool.success", False)
            tool_span.__exit__(type(e), e, e.__traceback__)
            telemetry.record_error(type(e).__name__, "tool.search_flights")
        
        logger.error(f"Error in search_flights tool: {e}")
        return f"❌ Erreur lors de la recherche: {str(e)}"


@tool
def search_hotels(destination: str, checkin_date: str, checkout_date: str, guests: int = 2) -> str:
    """Recherche des hôtels disponibles avec prix via Booking.com API.
    
    Args:
        destination: Ville de destination
        checkin_date: Date d'arrivée YYYY-MM-DD
        checkout_date: Date de départ YYYY-MM-DD
        guests: Nombre de voyageurs
    
    Returns:
        Liste des hôtels avec prix
    """
    telemetry = get_telemetry()
    start_time = time.time()
    
    # Créer un span pour l'exécution du tool
    if telemetry:
        tool_span = telemetry.trace_tool_call("search_hotels")
        span = tool_span.__enter__()
        span.set_attribute("tool.destination", destination)
        span.set_attribute("tool.checkin_date", checkin_date)
        span.set_attribute("tool.checkout_date", checkout_date)
        span.set_attribute("tool.guests", guests)
    
    try:
        from services.hotel_service import get_hotel_service
        
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        nights = (checkout - checkin).days
        
        # Search hotels using Booking.com API
        hotel_service = get_hotel_service()
        hotels = hotel_service.search(destination, checkin_date, checkout_date, guests)
        
        if not hotels:
            return f"❌ Aucun hôtel trouvé à {destination}"
        
        result = f"🏨 Hôtels à {destination} ({nights} nuits, {guests} voyageurs):\n\n"
        
        for i, hotel in enumerate(hotels, 1):
            result += f"{i}. **{hotel.name}** - {hotel.stars}⭐\n"
            result += f"   ${hotel.total_price:.0f} total (${hotel.price_per_night:.0f}/nuit)\n"
            
            if hotel.rating:
                result += f"   📊 Note: {hotel.rating}/10"
                if hotel.review_count:
                    result += f" ({hotel.review_count} avis)"
                result += "\n"
            
            if hotel.address:
                result += f"   📍 {hotel.address}\n"
            
            result += "\n"
        
        # Find cheapest
        cheapest = min(hotels, key=lambda x: x.price_per_night)
        result += f"💰 Meilleur prix: ${cheapest.total_price:.0f} - {cheapest.name}"
        
        # Enregistrer les métriques de succès
        if telemetry:
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("tool.result_count", len(hotels))
            span.set_attribute("tool.latency_ms", latency_ms)
            span.set_attribute("tool.success", True)
            tool_span.__exit__(None, None, None)
            telemetry.record_tool_call("search_hotels", latency_ms, True)
        
        return result
        
    except Exception as e:
        # Enregistrer l'erreur dans le span
        if telemetry:
            span.record_exception(e)
            span.set_attribute("tool.success", False)
            tool_span.__exit__(type(e), e, e.__traceback__)
            telemetry.record_error(type(e).__name__, "tool.search_hotels")
        
        logger.error(f"Error in search_hotels tool: {e}")
        return f"❌ Erreur: {str(e)}"


@tool  
def calculate_total_cost(flight_price: float, hotel_price: float, travelers: int = 2) -> str:
    """Calcule le coût total du voyage.
    
    Args:
        flight_price: Prix du vol par personne
        hotel_price: Prix total de l'hôtel
        travelers: Nombre de voyageurs
    
    Returns:
        Détail du coût total
    """
    try:
        total_flights = flight_price * travelers
        total_cost = total_flights + hotel_price
        cost_per_person = total_cost / travelers
        
        result = "💵 COÛT TOTAL:\n\n"
        result += f"Vols: ${flight_price}/pers × {travelers} = ${total_flights}\n"
        result += f"Hôtel: ${hotel_price}\n"
        result += f"{'─' * 30}\n"
        result += f"TOTAL: ${total_cost} pour {travelers} personnes\n"
        result += f"Soit ${cost_per_person:.0f}/personne"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in calculate_total_cost: {e}")
        return f"❌ Erreur de calcul: {str(e)}"


@tool
def search_vacation_rentals(destination: str, checkin_date: str, checkout_date: str, guests: int = 2) -> str:
    """Recherche des locations de vacances (appartements, maisons) via API réelles.
    
    Args:
        destination: Ville de destination
        checkin_date: Date d'arrivée YYYY-MM-DD
        checkout_date: Date de départ YYYY-MM-DD
        guests: Nombre de voyageurs
    
    Returns:
        Liste formatée des locations avec prix
    """
    try:
        service = get_rental_service()
        rentals = service.search_rentals(destination, checkin_date, checkout_date, guests)
        
        if not rentals:
            return f"❌ Aucune location trouvée à {destination}"
        
        result = f"🏠 Locations de vacances à {destination}:\n\n"
        result += service.format_rentals_for_display(rentals)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_vacation_rentals tool: {e}")
        return f"❌ Erreur lors de la recherche: {str(e)}"


@tool
def find_nearby_attractions(city: str, hotel_address: str = None, radius_km: float = 3.0) -> str:
    """Trouve les attractions touristiques et lieux historiques près d'un hôtel.
    
    Utilise OpenStreetMap pour géolocaliser et Overpass API pour trouver:
    - Monuments historiques
    - Musées
    - Sites archéologiques
    - Châteaux et fortifications
    - Points de vue
    - Galeries d'art
    
    Args:
        city: Ville de destination
        hotel_address: Adresse de l'hôtel (optionnel, sinon centre-ville)
        radius_km: Rayon de recherche en km (défaut: 3 km)
    
    Returns:
        Liste formatée des attractions avec distances et liens Wikipedia
    """
    try:
        location_service = get_location_service()
        
        # Géolocaliser l'adresse ou le centre-ville
        query = hotel_address if hotel_address else city
        location = location_service.geocode_address(query, city)
        
        if not location:
            return f"❌ Impossible de géolocaliser: {query}"
        
        # Trouver les attractions autour
        attractions = location_service.find_nearby_attractions(
            location.latitude,
            location.longitude,
            radius_km=radius_km,
            max_results=15
        )
        
        if not attractions:
            return f"❌ Aucune attraction trouvée dans un rayon de {radius_km} km"
        
        # Formater le résultat
        result = f"📍 Attractions près de {city}"
        if hotel_address:
            result += f" ({hotel_address})"
        result += f" - Rayon {radius_km} km:\n\n"
        
        # Grouper par type
        by_type = {}
        for attr in attractions:
            attr_type = attr.type
            if attr_type not in by_type:
                by_type[attr_type] = []
            by_type[attr_type].append(attr)
        
        # Afficher par catégorie
        type_icons = {
            'monument': '🗿',
            'museum': '🏛️',
            'castle': '🏰',
            'church': '⛪',
            'memorial': '🕊️',
            'attraction': '⭐',
            'ruins': '🏛️',
            'fort': '🏰',
            'gallery': '🎨',
            'viewpoint': '👁️'
        }
        
        for attr_type, attrs in sorted(by_type.items()):
            icon = type_icons.get(attr_type, '📌')
            result += f"\n{icon} {attr_type.upper()}:\n"
            
            for attr in attrs[:5]:  # Max 5 par catégorie
                result += f"\n• {attr.name} - {attr.distance_km} km\n"
                
                if attr.description:
                    desc = attr.description[:80] + "..." if len(attr.description) > 80 else attr.description
                    result += f"  {desc}\n"
                
                if attr.address:
                    result += f"  📍 {attr.address}\n"
                
                if attr.wikipedia_url:
                    result += f"  🔗 {attr.wikipedia_url}\n"
        
        result += f"\n\n💡 Total: {len(attractions)} attractions trouvées"
        result += f"\n📊 Carte interactive disponible avec generate_travel_map"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_nearby_attractions tool: {e}")
        return f"❌ Erreur lors de la recherche: {str(e)}"


@tool
def generate_travel_map(city: str, hotel_addresses: str, output_file: str = "travel_map.html") -> str:
    """Génère une carte interactive HTML avec hôtels et attractions touristiques.
    
    Args:
        city: Ville de destination
        hotel_addresses: Adresses des hôtels séparées par des virgules
        output_file: Nom du fichier HTML (défaut: travel_map.html)
    
    Returns:
        Confirmation de génération avec chemin du fichier
    """
    try:
        from services.location_service import Location
        
        location_service = get_location_service()
        
        # Géolocaliser les hôtels
        addresses = [addr.strip() for addr in hotel_addresses.split(',')]
        locations = []
        
        for address in addresses:
            loc = location_service.geocode_address(address, city)
            if loc:
                loc.type = 'hotel'
                locations.append(loc)
        
        # Si aucun hôtel géolocalisé, utiliser le centre-ville
        if not locations:
            print(f"⚠️ Aucun hôtel géolocalisé, utilisation du centre de {city}")
            center = location_service.geocode_address(city, "")
            if not center:
                return f"❌ Impossible de géolocaliser {city}"
            center.type = 'city_center'
            locations.append(center)
        
        # Trouver les attractions autour du premier hôtel
        attractions = location_service.find_nearby_attractions(
            locations[0].latitude,
            locations[0].longitude,
            radius_km=3.0,
            max_results=20
        )
        
        # Générer la carte
        map_path = location_service.generate_map(locations, attractions, output_file)
        
        if not map_path:
            return "❌ Erreur lors de la génération de la carte"
        
        result = f"✅ Carte interactive générée!\n\n"
        result += f"📁 Fichier: {map_path}\n"
        result += f"🏨 Hôtels: {len(locations)}\n"
        result += f"📍 Attractions: {len(attractions)}\n\n"
        result += f"Ouvrez {output_file} dans votre navigateur pour voir la carte."
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_travel_map tool: {e}")
        return f"❌ Erreur: {str(e)}"


@tool
def find_cultural_activities(
    city: str,
    preferences: str = "art,history",
    radius_km: float = 5.0
) -> str:
    """Trouve des activités culturelles (musées, galeries, monuments) selon les goûts.
    
    Permet de découvrir les incontournables culturels et de filtrer par préférences:
    - art: Musées d'art, galeries
    - history: Musées historiques, sites archéologiques
    - science: Musées de sciences, planétariums
    - architecture: Monuments architecturaux
    - performing_arts: Théâtres, opéras
    
    Args:
        city: Ville de destination
        preferences: Préférences séparées par virgules (ex: "art,history")
        radius_km: Rayon de recherche en km (défaut: 5 km)
    
    Returns:
        Liste formatée des activités culturelles avec horaires et prix
    """
    try:
        from services.location_service import get_location_service
        
        # Géolocaliser directement la ville
        location_service = get_location_service()
        location = location_service.geocode_address(city, "")
        
        if not location:
            return f"❌ Impossible de géolocaliser {city}"
        
        # Convertir les préférences en liste
        pref_list = [p.strip() for p in preferences.split(',')]
        
        # Trouver les activités
        cultural_service = get_cultural_service()
        activities = cultural_service.find_cultural_activities(
            city=city,
            latitude=location.latitude,
            longitude=location.longitude,
            preferences=pref_list,
            radius_km=radius_km,
            max_results=10
        )
        
        if not activities:
            return f"❌ Aucune activité culturelle trouvée à {city}"
        
        # Formater le résultat
        result = f"🎨 Activités culturelles à {city}:\n"
        result += f"Préférences: {', '.join(pref_list)}\n\n"
        result += cultural_service.format_activities_for_display(activities)
        
        # Ajouter conseil de réservation
        must_see_count = sum(1 for a in activities if a.must_see)
        if must_see_count > 0:
            result += f"\n💡 {must_see_count} incontournable(s) identifié(s) - Réservation recommandée !"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_cultural_activities tool: {e}")
        return f"❌ Erreur lors de la recherche: {str(e)}"


@tool
def recommend_restaurants(
    city: str,
    cuisine_types: str = "local",
    budget: str = "$$",
    radius_km: float = 3.0
) -> str:
    """Recommande des restaurants selon les goûts culinaires et le budget.
    
    Types de cuisine disponibles:
    - local: Cuisine locale/traditionnelle
    - french: Cuisine française
    - italian: Cuisine italienne
    - asian: Cuisine asiatique
    - american: Cuisine américaine
    - fusion: Cuisine fusion/créative
    
    Niveaux de budget:
    - $: Économique (< 15€/pers)
    - $$: Moyen (15-30€/pers)
    - $$$: Élevé (30-60€/pers)
    - $$$$: Très élevé (> 60€/pers)
    
    Args:
        city: Ville de destination
        cuisine_types: Types de cuisine séparés par virgules (ex: "local,french")
        budget: Budget souhaité ('$' à '$$$$')
        radius_km: Rayon de recherche en km (défaut: 3 km)
    
    Returns:
        Liste formatée des restaurants avec spécialités et coordonnées
    """
    try:
        from services.location_service import get_location_service
        
        # Géolocaliser directement la ville
        location_service = get_location_service()
        location = location_service.geocode_address(city, "")
        
        if not location:
            return f"❌ Impossible de géolocaliser {city}"
        
        # Convertir les types de cuisine en liste
        cuisine_list = [c.strip() for c in cuisine_types.split(',')]
        
        # Trouver les restaurants
        restaurant_service = get_restaurant_service()
        restaurants = restaurant_service.find_restaurants(
            city=city,
            latitude=location.latitude,
            longitude=location.longitude,
            cuisine_preferences=cuisine_list,
            budget=budget,
            radius_km=radius_km,
            max_results=8
        )
        
        if not restaurants:
            return f"❌ Aucun restaurant trouvé à {city} avec ces critères"
        
        # Formater le résultat
        result = f"🍽️ Restaurants recommandés à {city}:\n"
        result += f"Cuisine: {', '.join(cuisine_list)} | Budget: {budget}\n\n"
        result += restaurant_service.format_restaurants_for_display(restaurants)
        
        # Ajouter conseil
        result += "\n💡 Conseil: Réservation recommandée pour les restaurants les mieux notés!"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in recommend_restaurants tool: {e}")
        return f"❌ Erreur lors de la recherche: {str(e)}"


@tool
def create_visit_itinerary(
    city: str,
    duration_days: int,
    interests: str = "culture,food,attractions"
) -> str:
    """Crée un itinéraire de visite jour par jour avec musées, restaurants et attractions.
    
    Génère un planning optimisé avec:
    - Activités culturelles le matin
    - Déjeuner dans restaurants sélectionnés
    - Visites touristiques l'après-midi
    - Dîner recommandé
    
    Intérêts disponibles:
    - culture: Musées, galeries, monuments
    - food: Restaurants, gastronomie locale
    - attractions: Sites touristiques, panoramas
    - history: Sites historiques, patrimoine
    - art: Musées d'art, galeries
    
    Args:
        city: Ville de destination
        duration_days: Nombre de jours (1-7)
        interests: Centres d'intérêt séparés par virgules
    
    Returns:
        Itinéraire détaillé jour par jour avec horaires suggérés
    """
    try:
        from services.location_service import get_location_service
        
        # Limiter la durée
        duration_days = min(duration_days, 7)
        
        # Géolocaliser directement la ville (pas "centre ville")
        location_service = get_location_service()
        
        print(f"🔍 Searching itinerary for: {city}")
        location = location_service.geocode_address(city, "")
        
        if not location:
            return f"❌ Impossible de géolocaliser {city}"
        
        # Parser les intérêts
        interest_list = [i.strip() for i in interests.split(',')]
        
        # Définir les préférences culturelles et culinaires
        cultural_prefs = []
        if 'culture' in interest_list or 'art' in interest_list:
            cultural_prefs.extend(['art', 'architecture'])
        if 'history' in interest_list:
            cultural_prefs.append('history')
        
        if not cultural_prefs:
            cultural_prefs = ['art', 'history']
        
        # Récupérer activités et restaurants
        cultural_service = get_cultural_service()
        restaurant_service = get_restaurant_service()
        
        activities = cultural_service.find_cultural_activities(
            city=city,
            latitude=location.latitude,
            longitude=location.longitude,
            preferences=cultural_prefs,
            max_results=duration_days * 2
        )
        
        restaurants = restaurant_service.find_restaurants(
            city=city,
            latitude=location.latitude,
            longitude=location.longitude,
            cuisine_preferences=['local'],
            budget='$$',
            max_results=duration_days * 2
        )
        
        # Créer l'itinéraire
        result = f"📅 ITINÉRAIRE {duration_days} JOURS À {city.upper()}\n"
        result += f"Centres d'intérêt: {', '.join(interest_list)}\n\n"
        result += "="*60 + "\n\n"
        
        for day in range(1, duration_days + 1):
            result += f"🗓️ JOUR {day}\n"
            result += "-" * 40 + "\n\n"
            
            # Matin: Activité culturelle
            if activities:
                morning_activity = activities[(day - 1) * 2 % len(activities)]
                result += f"🌅 MATIN (9h-12h)\n"
                result += f"   {morning_activity.name}\n"
                result += f"   📍 {morning_activity.address}\n"
                result += f"   💰 {morning_activity.price_range} | ⏱️ {morning_activity.estimated_duration}\n"
                if morning_activity.must_see:
                    result += f"   ⭐ INCONTOURNABLE\n"
                result += "\n"
            
            # Déjeuner
            if restaurants:
                lunch_resto = restaurants[day % len(restaurants)]
                result += f"🍽️ DÉJEUNER (12h30-14h)\n"
                result += f"   {lunch_resto.name} - {lunch_resto.cuisine_type}\n"
                result += f"   📍 {lunch_resto.address}\n"
                result += f"   💰 {lunch_resto.price_range} | ⭐ {lunch_resto.rating}/5\n"
                result += "\n"
            
            # Après-midi: Autre activité
            if len(activities) > day:
                afternoon_activity = activities[(day - 1) * 2 + 1 if day * 2 <= len(activities) else 0]
                result += f"☀️ APRÈS-MIDI (15h-18h)\n"
                result += f"   {afternoon_activity.name}\n"
                result += f"   📍 {afternoon_activity.address}\n"
                result += f"   💰 {afternoon_activity.price_range}\n"
                result += "\n"
            
            # Dîner
            if len(restaurants) > day:
                dinner_resto = restaurants[(day + 1) % len(restaurants)]
                result += f"🌙 DÎNER (19h30-22h)\n"
                result += f"   {dinner_resto.name} - {dinner_resto.cuisine_type}\n"
                result += f"   📍 {dinner_resto.address}\n"
                result += f"   💰 {dinner_resto.price_range} | ⭐ {dinner_resto.rating}/5\n"
                result += "\n"
            
            result += "\n"
        
        result += "="*60 + "\n"
        result += "💡 Conseils:\n"
        result += "• Réservez les musées incontournables à l'avance\n"
        result += "• Réservez les restaurants le soir (haute saison)\n"
        result += "• Prévoyez du temps pour flâner entre les visites\n"
        result += "• Utilisez generate_travel_map pour visualiser l'itinéraire\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_visit_itinerary tool: {e}")
        return f"❌ Erreur lors de la création de l'itinéraire: {str(e)}"

@tool
def get_destination_context(city: str) -> str:
    """Récupère le contexte culturel, climatique et gastronomique d'une destination depuis Wikipedia.
    
    Utilisez cet outil AVANT de planifier un voyage pour enrichir vos recommandations avec:
    - Histoire et culture de la ville
    - Climat et meilleures périodes
    - Spécialités gastronomiques
    - Points d'intérêt emblématiques
    
    Args:
        city: Nom de la ville (ex: 'Osaka', 'Paris', 'Tunis')
    
    Returns:
        Contexte enrichi formaté pour améliorer les recommandations
    """
    try:
        service = get_wikipedia_service()
        
        # Essayer plusieurs langues pour maximiser les chances de succès
        for lang in ['fr', 'en']:
            context = service.get_city_context(city, lang=lang)
            if context:
                result = "📚 CONTEXTE DESTINATION\n"
                result += "="*60 + "\n\n"
                result += context.to_prompt()
                result += "\n\n💡 Utilisez ce contexte pour personnaliser vos recommandations\n"
                return result
        
        return f"ℹ️ Aucun contexte Wikipedia trouvé pour {city}"
        
    except Exception as e:
        logger.error(f"Error in get_destination_context tool: {e}")
        return f"⚠️ Erreur lors de la récupération du contexte: {str(e)}"


@tool
def recommend_best_package(
    packages_info: str,
    user_budget: str = "medium",
    travel_style: str = "balanced",
    priorities: str = "value"
) -> str:
    """Recommande le meilleur package vol+hébergement avec analyse comparative détaillée.
    
    Analyse INTELLIGENTE comparant hôtels vs locations, packages vol+hôtel combinés.
    Recommande la meilleure option selon budget, style et priorités avec justifications détaillées.
    
    Args:
        packages_info: Détails packages "Package1: $X (vol+hôtel), Package2: $Y (vol+location)"
        user_budget: "low" (<$2000), "medium" ($2000-5000), "high" (>$5000)
        travel_style: "budget" (économies max), "balanced" (équilibre), "luxury" (confort premium)
        priorities: "value" (qualité/prix), "comfort" (confort max), "adventure" (authenticité)
    
    Returns:
        Analyse comparative complète hôtels vs locations avec recommandation justifiée
    """
    try:
        result = "\n" + "="*70 + "\n"
        result += "🎯 RECOMMANDATION INTELLIGENTE - ANALYSE COMPARATIVE\n"
        result += "="*70 + "\n\n"
        
        # Profil utilisateur
        budget_map = {"low": "Économique (<$2000)", "medium": "Standard ($2000-5000)", "high": "Confort (>$5000)"}
        style_map = {"budget": "Économique (max économies)", "balanced": "Équilibré (confort+prix)", "luxury": "Luxueux (premium)"}
        priority_map = {
            "value": "Meilleur rapport qualité/prix",
            "comfort": "Confort et services maximum",
            "adventure": "Expériences authentiques et immersion locale"
        }
        
        result += "📊 VOTRE PROFIL:\n"
        result += f"   • Budget: {budget_map.get(user_budget, 'Standard')}\n"
        result += f"   • Style: {style_map.get(travel_style, 'Équilibré')}\n"
        result += f"   • Priorité: {priority_map.get(priorities, 'Rapport qualité/prix')}\n"
        result += "\n" + "-"*70 + "\n\n"
        
        # Détection hôtel vs location dans packages_info
        has_hotel = "hôtel" in packages_info.lower() or "hotel" in packages_info.lower()
        has_rental = "location" in packages_info.lower() or "airbnb" in packages_info.lower()
        
        # Logique de recommandation intelligente
        if travel_style == "budget" or user_budget == "low":
            recommendation = "Package 1 (Économique)"
            reason_title = "💰 BUDGET OPTIMISÉ"
            reasons = [
                "✓ Prix le plus bas tout en gardant qualité",
                "✓ Économies hébergement = plus pour activités",
                "✓ Locations avec cuisine = -25% budget repas"
            ]
            
            comparison = "🏠 LOCATION RECOMMANDÉE:\n"
            comparison += "   • Cuisine équipée : économie $30-50/jour repas\n"
            comparison += "   • Espace supérieur : séjour + chambres séparées\n"
            comparison += "   • Authenticité : quartiers locaux, vie quotidienne\n"
            comparison += "   • Flexibilité totale : horaires, style de vie\n"
            
            tip = "💡 ASTUCE: Cuisine = économie $200-300 sur 7 jours (petits-déjeuners + 2-3 dîners) !"
            
        elif travel_style == "luxury" or user_budget == "high":
            recommendation = "Package 3-4 (Premium)"
            reason_title = "⭐ CONFORT PREMIUM"
            reasons = [
                "✓ Hôtels 4-5⭐: services complets, standing élevé",
                "✓ Services inclus: ménage, concierge, petit-déjeuner",
                "✓ Localisation premium: centre-ville, sites majeurs",
                "✓ Tranquillité: pas de gestion, tout organisé"
            ]
            
            comparison = "🏨 HÔTEL PREMIUM:\n"
            comparison += "   • Services 24h: réception, concierge, room service\n"
            comparison += "   • Ménage quotidien + linge frais + produits luxe\n"
            comparison += "   • Équipements: spa, piscine, fitness, restaurant\n"
            comparison += "   • Localisation centrale: à pied sites majeurs\n"
            
            tip = "💡 ASTUCE: Hôtels 5⭐ incluent petit-déjeuner ($25/pers) + WiFi premium + transferts !"
            
        else:  # balanced/medium
            if priorities == "value":
                recommendation = "Package 2 (Équilibré) ⭐ MEILLEUR CHOIX"
                reason_title = "🎯 RAPPORT QUALITÉ/PRIX OPTIMAL"
                reasons = [
                    "✓ Compromis parfait: bon confort + prix raisonnable",
                    "✓ Hôtel 3-4⭐ ou Location premium selon préférence",
                    "✓ Budget restant pour activités et restaurants qualité",
                    "✓ Flexibilité: peut mixer hôtel début + location fin"
                ]
                
                comparison = "⚖️ COMPARAISON DÉTAILLÉE:\n\n"
                comparison += "🏨 HÔTEL 3-4⭐ (~$150-200/nuit):\n"
                comparison += "   ✓ Services: ménage quotidien, réception 24h\n"
                comparison += "   ✓ Localisation: centre-ville, transports\n"
                comparison += "   ✗ Pas de cuisine: tous repas restaurant\n"
                comparison += "   ✗ Espace limité: chambre standard\n\n"
                comparison += "🏠 LOCATION PREMIUM (~$100-150/nuit):\n"
                comparison += "   ✓ Espace: séjour + cuisine + 1-2 chambres\n"
                comparison += "   ✓ Économies: cuisine = -$35/jour repas\n"
                comparison += "   ✓ Authenticité: quartier local, marché\n"
                comparison += "   ✗ Self check-in, ménage par vous\n\n"
                comparison += "💡 VERDICT: Location premium = Meilleur rapport qualité/prix !"
                
                tip = "💡 ASTUCE: Location = économie $400-700 sur séjour (hébergement+repas) + authenticité !"
                
            elif priorities == "comfort":
                recommendation = "Package 2-3 (Équilibré vers Premium)"
                reason_title = "🛋️ CONFORT PRIORITAIRE"
                reasons = [
                    "✓ Package 2: Hôtel 4⭐ déjà excellent confort",
                    "✓ Package 3: Si budget ok, hôtel 5⭐ luxe total",
                    "✓ Services hôteliers: tranquillité + assistance",
                    "✓ Localisation premium: moins de déplacements"
                ]
                
                comparison = "🏨 HÔTEL RECOMMANDÉ:\n"
                comparison += "   • Ménage quotidien: chambre impeccable chaque jour\n"
                comparison += "   • Support 24h: réception, concierge, urgences\n"
                comparison += "   • Équipements confort: literie premium, spa, piscine\n"
                comparison += "   • Sécurité max: accès sécurisé, coffre, surveillance\n"
                
                tip = "💡 ASTUCE: Vérifiez notes confort Booking.com (8.5+) + avis literie/propreté !"
                
            else:  # adventure
                recommendation = "Package 1-2 avec LOCATION"
                reason_title = "🌍 EXPÉRIENCE AUTHENTIQUE"
                reasons = [
                    "✓ Économies hébergement = plus d'activités uniques",
                    "✓ Quartiers locaux: immersion culturelle vraie",
                    "✓ Marchés + cuisine: découverte gastronomique",
                    "✓ Hôtes locaux: bons plans secrets, rencontres"
                ]
                
                comparison = "🏠 LOCATION AUTHENTIQUE:\n"
                comparison += "   • Quartiers résidentiels: vie locale quotidienne\n"
                comparison += "   • Marchés du coin: produits frais, cuisine locale\n"
                comparison += "   • Interaction hôtes: conseils restaurants, sites cachés\n"
                comparison += "   • Liberté totale: horaires flexibles, pas de contraintes\n"
                
                tip = "💡 ASTUCE: Quartier non-touristique + transports = vraie immersion + facilité accès !"
        
        result += f"{reason_title}\n"
        result += f"✅ RECOMMANDATION: {recommendation}\n\n"
        result += "📝 POURQUOI:\n"
        for reason in reasons:
            result += f"   {reason}\n"
        result += "\n" + "-"*70 + "\n\n"
        
        result += comparison + "\n"
        result += "-"*70 + "\n\n"
        result += f"{tip}\n\n"
        
        # Tableau comparatif
        result += "📊 TABLEAU COMPARATIF:\n\n"
        result += "┌─────────────┬──────────────┬─────────────────┬──────────────────┐\n"
        result += "│ Package     │ Type Héberg. │ Confort         │ Rapport Q/P      │\n"
        result += "├─────────────┼──────────────┼─────────────────┼──────────────────┤\n"
        result += "│ Package 1   │ Location     │ ⭐⭐⭐         │ ⭐⭐⭐⭐⭐      │\n"
        result += "│ (Économique)│ Airbnb       │ Basique/Moyen   │ Excellent        │\n"
        result += "├─────────────┼──────────────┼─────────────────┼──────────────────┤\n"
        result += "│ Package 2   │ Hôtel 3-4⭐   │ ⭐⭐⭐⭐       │ ⭐⭐⭐⭐        │\n"
        result += "│ (Équilibré) │ ou Location+ │ Bon confort     │ Très bon         │\n"
        result += "├─────────────┼──────────────┼─────────────────┼──────────────────┤\n"
        result += "│ Package 3   │ Hôtel 4-5⭐   │ ⭐⭐⭐⭐⭐     │ ⭐⭐⭐          │\n"
        result += "│ (Premium)   │ Services+    │ Luxe            │ Correct          │\n"
        result += "└─────────────┴──────────────┴─────────────────┴──────────────────┘\n\n"
        
        # Économies
        result += "💵 ÉCONOMIES AVEC LOCATIONS:\n"
        result += "   • Hébergement: -30% vs hôtel équivalent ($50-100/nuit)\n"
        result += "   • Repas cuisine: -40% sur budget food ($30-50/jour)\n"
        result += "   • Total 7 jours: $350-700 économisés (hors vol)\n"
        result += "   • Argent dispo: Activités premium, excursions\n\n"
        
        # Packages combinés
        result += "✈️ PACKAGES VOL+HÔTEL:\n"
        result += "   Les packages combinent vol + hébergement.\n"
        result += "   Analysez le TOTAL (pas seulement l'hébergement):\n"
        result += "   • Package économique = Max budget activités\n"
        result += "   • Package équilibré = Confort raisonnable\n"
        result += "   • Package premium = Luxe sans compromis\n\n"
        
        result += "="*70 + "\n"
        result += "💬 Choisissez selon vos priorités !\n"
        result += "="*70 + "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in recommend_best_package: {e}")
        return f"❌ Erreur: {str(e)}"


def create_all_tools():
    """
    Retourne la liste de tous les outils disponibles pour l'agent.
    
    Returns:
        Liste de tous les outils LangChain
    """
    return [
        get_airport_code,
        get_destination_context,
        search_flights,
        search_hotels,
        search_vacation_rentals,
        find_cultural_activities,
        find_nearby_attractions,
        recommend_restaurants,
        create_visit_itinerary,
        generate_travel_map,
        calculate_total_cost,
        recommend_best_package
    ]
