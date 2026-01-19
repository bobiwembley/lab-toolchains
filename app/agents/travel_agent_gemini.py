"""
Template Gemini 2.0 Flash - Google Vertex AI
Configuration optimisée pour Gemini avec vitesse et économie
"""

from typing import List
from langchain_core.tools import BaseTool
from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider


class GeminiTravelAgent(TravelAgent):
    """
    Travel Agent spécialisé pour Gemini 2.0 Flash
    
    Caractéristiques:
    - Très rapide (2-3x plus rapide que Claude)
    - Coût 98% inférieur à Claude
    - Multimodal natif (images, vidéo)
    - Excellent pour tâches répétitives
    - Coût: $0.075/$0.30 par million de tokens
    
    Prérequis:
    1. Installer Google Cloud SDK: 
       curl https://sdk.cloud.google.com | bash
       
    2. S'authentifier:
       gcloud auth application-default login
       
    3. Configurer le projet:
       export GOOGLE_CLOUD_PROJECT="your-project-id"
       
    4. Activer Vertex AI:
       gcloud services enable aiplatform.googleapis.com
    
    Usage:
        tools = [...]
        agent = GeminiTravelAgent(tools=tools)
        response = agent.plan_trip("Voyage à Tokyo")
    """
    
    def __init__(
        self,
        tools: List[BaseTool],
        temperature: float = 0.5
    ):
        """
        Initialize Gemini Travel Agent
        
        Args:
            tools: Liste des outils LangChain
            temperature: Température du modèle (0-1)
                - 0.3-0.5: Réponses focalisées (recommandé pour voyage)
                - 0.6-0.9: Plus créatif, varié
        """
        super().__init__(
            tools=tools,
            model_provider=ModelProvider.GEMINI,
            temperature=temperature
        )
        
    @staticmethod
    def get_recommended_settings() -> dict:
        """
        Retourne les paramètres recommandés pour Gemini
        
        Returns:
            Dict avec les settings optimaux
        """
        return {
            "temperature": 0.5,  # Équilibre entre cohérence et créativité
            "max_tokens": 3072,  # Pour réponses détaillées
            "max_iterations": 5,  # Permet tous les outils
            "use_cases": [
                "Recherches répétitives (quotidiennes)",
                "Recommandations standards rapides",
                "Budget limité (POC, MVP)",
                "Haute fréquence d'utilisation",
            ],
            "strengths": [
                "Vitesse d'exécution exceptionnelle",
                "Coût extrêmement bas (98% moins cher)",
                "Multimodal natif (images, vidéos)",
                "Scalabilité économique",
            ],
            "pricing": {
                "input": "$0.075 / 1M tokens",
                "output": "$0.30 / 1M tokens",
                "estimated_per_search": "$0.0016",
                "monthly_300_searches": "$0.48",
                "savings_vs_claude": "-98%",
            },
            "setup_required": {
                "gcloud_cli": "Google Cloud SDK",
                "authentication": "Application Default Credentials",
                "vertex_ai": "Vertex AI API activée",
                "project_id": "GOOGLE_CLOUD_PROJECT env var",
            }
        }
    
    @staticmethod
    def print_setup_instructions():
        """
        Affiche les instructions de setup pour Vertex AI
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║           SETUP GEMINI 2.0 FLASH (VERTEX AI)                    ║
╚══════════════════════════════════════════════════════════════════╝

1️⃣  INSTALLER GOOGLE CLOUD SDK:
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL

2️⃣  S'AUTHENTIFIER (Application Default Credentials):
   gcloud auth application-default login
   
   ⚠️  Suivez le lien dans le navigateur et autorisez l'accès

3️⃣  CRÉER/SÉLECTIONNER UN PROJET:
   gcloud projects create lab-toolchains-ai --name="Lab AI"
   gcloud config set project lab-toolchains-ai

4️⃣  ACTIVER VERTEX AI API:
   gcloud services enable aiplatform.googleapis.com

5️⃣  CONFIGURER L'ENVIRONNEMENT (.env):
   GOOGLE_CLOUD_PROJECT=lab-toolchains-ai

6️⃣  TESTER LA CONFIGURATION:
   python -c "from agents.travel_agent_gemini import GeminiTravelAgent; \\
              print('✅ Gemini ready!')"

╔══════════════════════════════════════════════════════════════════╗
║                      COÛTS COMPARATIFS                           ║
╚══════════════════════════════════════════════════════════════════╝

Claude Sonnet 4:        $0.069 / recherche  →  $21 / mois (300 req)
Gemini 2.0 Flash:       $0.0016 / recherche →  $0.48 / mois (300 req)

💰 ÉCONOMIE: -98% (-$20.52/mois)

╔══════════════════════════════════════════════════════════════════╗
║                    QUAND UTILISER GEMINI?                        ║
╚══════════════════════════════════════════════════════════════════╝

✅ POC / MVP avec budget serré
✅ Recherches fréquentes (>100/jour)
✅ Application en production avec scaling
✅ Besoin de vitesse d'exécution
✅ Multimodal (images de destinations)

❌ Planification très complexe multi-destination
❌ Besoin de raisonnement nuancé poussé
❌ Budget illimité privilégiant la qualité maximale
""")
