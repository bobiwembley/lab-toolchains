"""
Service d'enrichissement contextuel via Wikipedia et Wikidata.
Optimisé pour réduire les tokens et maximiser la pertinence.
"""

import requests
import logging
from functools import lru_cache
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CityContext:
    """Contexte enrichi d'une ville"""
    name: str
    summary: str
    population: Optional[int] = None
    timezone: Optional[str] = None
    known_for: list = None
    climate_info: Optional[str] = None
    
    def to_prompt(self) -> str:
        """Convertit le contexte en prompt compact pour l'agent"""
        parts = [f"📍 {self.name}"]
        
        if self.summary:
            parts.append(f"\n{self.summary}")
        
        if self.population:
            pop_str = f"{self.population:,}".replace(',', ' ')
            parts.append(f"\n👥 Population: {pop_str} habitants")
        
        if self.known_for:
            parts.append(f"\n⭐ Réputée pour: {', '.join(self.known_for)}")
        
        if self.climate_info:
            parts.append(f"\n🌡️ Climat: {self.climate_info}")
        
        return ''.join(parts)


class WikipediaService:
    """Service pour récupérer le contexte enrichi d'une ville"""
    
    def __init__(self):
        self.wiki_api = "https://fr.wikipedia.org/api/rest_v1/page/summary"
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        self.user_agent = "TravelAgent/1.0"
    
    @lru_cache(maxsize=500)
    def get_city_context(self, city: str, lang: str = "fr") -> Optional[CityContext]:
        """
        Récupère le contexte enrichi d'une ville (avec cache de 500 villes)
        
        Args:
            city: Nom de la ville
            lang: Langue Wikipedia (fr, en, ja, etc.)
            
        Returns:
            CityContext ou None si non trouvé
        """
        try:
            # 1. Récupérer le résumé Wikipedia (léger, déjà formaté)
            summary = self._get_wikipedia_summary(city, lang)
            
            if not summary:
                logger.warning(f"No Wikipedia summary for {city}")
                return None
            
            # 2. Extraire les infos structurées (optionnel, rapide)
            structured_data = self._extract_key_info(summary)
            
            context = CityContext(
                name=city,
                summary=summary['extract'][:400],  # Limiter à 400 chars (~100 tokens)
                known_for=structured_data.get('known_for', []),
                climate_info=structured_data.get('climate')
            )
            
            logger.info(f"✅ Wikipedia context retrieved for {city}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting Wikipedia context for {city}: {e}")
            return None
    
    def _get_wikipedia_summary(self, city: str, lang: str) -> Optional[Dict]:
        """Récupère le résumé Wikipedia (API REST, plus léger que l'article complet)"""
        try:
            # Essayer d'abord la langue demandée
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{city}"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers, timeout=5)
            
            # Si échec, essayer en anglais
            if response.status_code == 404 and lang != 'en':
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{city}"
                response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Wikipedia API error for {city}: {e}")
            return None
    
    def _extract_key_info(self, summary: Dict) -> Dict:
        """Extrait les infos clés du résumé Wikipedia"""
        extracted = {}
        
        text = summary.get('extract', '').lower()
        
        # Détecter les points d'intérêt (mots-clés)
        keywords = {
            'cuisine': ['gastronomie', 'cuisine', 'gastronomique', 'culinaire'],
            'culture': ['musée', 'art', 'culturel', 'patrimoine', 'unesco'],
            'histoire': ['historique', 'ancien', 'médiéval', 'château', 'monument'],
            'nature': ['plage', 'montagne', 'nature', 'parc', 'mer'],
            'moderne': ['moderne', 'technologie', 'innovation', 'métropole']
        }
        
        known_for = []
        for category, words in keywords.items():
            if any(word in text for word in words):
                known_for.append(category)
        
        extracted['known_for'] = known_for[:3]  # Max 3
        
        # Extraire info climat si présente
        if 'climat' in text or 'température' in text:
            # Simplifier l'extraction pour éviter trop de texte
            extracted['climate'] = 'tempéré' if 'tempéré' in text else 'variable'
        
        return extracted


# Singleton global
_wikipedia_service = None

def get_wikipedia_service() -> WikipediaService:
    """Retourne l'instance unique du service Wikipedia"""
    global _wikipedia_service
    if _wikipedia_service is None:
        _wikipedia_service = WikipediaService()
    return _wikipedia_service
