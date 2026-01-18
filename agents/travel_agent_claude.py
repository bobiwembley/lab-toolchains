"""
Template Claude Sonnet 4 - Anthropic API
Configuration optimisée pour Claude avec raisonnement avancé
"""

from typing import List
from langchain_core.tools import BaseTool
from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider


class ClaudeTravelAgent(TravelAgent):
    """
    Travel Agent spécialisé pour Claude Sonnet 4
    
    Caractéristiques:
    - Raisonnement complexe et nuancé
    - Excellente planification multi-étapes
    - Compréhension contextuelle profonde
    - Coût: $3/$15 par million de tokens
    
    Usage:
        tools = [...]
        agent = ClaudeTravelAgent(tools=tools)
        response = agent.plan_trip("Voyage à Tokyo")
    """
    
    def __init__(
        self,
        tools: List[BaseTool],
        temperature: float = 0.5
    ):
        """
        Initialize Claude Travel Agent
        
        Args:
            tools: Liste des outils LangChain
            temperature: Température du modèle (0-1)
                - 0.3-0.5: Réponses focalisées et cohérentes (recommandé)
                - 0.6-0.8: Plus créatif, diversifié
        """
        super().__init__(
            tools=tools,
            model_provider=ModelProvider.CLAUDE,
            temperature=temperature
        )
        
    @staticmethod
    def get_recommended_settings() -> dict:
        """
        Retourne les paramètres recommandés pour Claude
        
        Returns:
            Dict avec les settings optimaux
        """
        return {
            "temperature": 0.5,  # Équilibre entre cohérence et créativité
            "max_tokens": 3072,  # Pour réponses détaillées
            "max_iterations": 5,  # Permet tous les outils
            "use_cases": [
                "Planification complexe multi-destination",
                "Analyse nuancée budget vs confort",
                "Recommandations personnalisées sophistiquées",
                "Gestion de contraintes multiples",
            ],
            "strengths": [
                "Raisonnement en plusieurs étapes",
                "Compréhension des nuances culturelles",
                "Planification détaillée d'itinéraires",
                "Justifications approfondies des recommandations",
            ],
            "pricing": {
                "input": "$3.00 / 1M tokens",
                "output": "$15.00 / 1M tokens",
                "estimated_per_search": "$0.069",
                "monthly_300_searches": "$21",
            }
        }
