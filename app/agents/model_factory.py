"""
Factory pattern pour créer des instances de LLM (Claude ou Gemini).
Permet de switcher facilement entre les modèles.
"""
import os
from enum import Enum
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI


class ModelProvider(str, Enum):
    """Providers de modèles disponibles"""
    CLAUDE = "claude"
    GEMINI = "gemini"


class ModelFactory:
    """Factory pour créer des instances de LLM"""
    
    # Configuration des modèles
    CLAUDE_CONFIG = {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5,
        "max_tokens": 8192,
        "api_key_env": "ANTHROPIC_API_KEY",
    }
    
    GEMINI_CONFIG = {
        "model": "gemini-2.0-flash-001",
        "temperature": 0.5,
        "max_output_tokens": 8192,
        "project_env": "GOOGLE_CLOUD_PROJECT",
        "location": "us-central1",
    }
    
    @classmethod
    def create_llm(
        cls,
        provider: ModelProvider,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Crée une instance de LLM selon le provider choisi.
        
        Args:
            provider: Le provider de modèle (CLAUDE ou GEMINI)
            temperature: Override de température (optionnel)
            max_tokens: Override de max tokens (optionnel)
            
        Returns:
            Instance du LLM configuré
            
        Raises:
            ValueError: Si le provider n'est pas supporté ou si la config est invalide
        """
        if provider == ModelProvider.CLAUDE:
            return cls._create_claude(temperature, max_tokens)
        elif provider == ModelProvider.GEMINI:
            return cls._create_gemini(temperature, max_tokens)
        else:
            raise ValueError(f"Provider non supporté: {provider}")
    
    @classmethod
    def _create_claude(
        cls,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatAnthropic:
        """Crée une instance de Claude Sonnet 4"""
        config = cls.CLAUDE_CONFIG.copy()
        
        # Vérifier la clé API
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(f"Variable d'environnement {config['api_key_env']} non définie")
        
        # Override params si fournis
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens
        
        return ChatAnthropic(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            api_key=api_key,
            # Prompt caching activé via cache_control dans les messages
            # Voir: https://docs.anthropic.com/claude/docs/prompt-caching
        )
    
    @classmethod
    def _create_gemini(
        cls,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatVertexAI:
        """Crée une instance de Gemini 2.0 Flash"""
        config = cls.GEMINI_CONFIG.copy()
        
        # Vérifier le project ID (optionnel pour Vertex AI avec ADC)
        project = os.getenv(config["project_env"])
        
        # Override params si fournis
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
        
        return ChatVertexAI(
            model=config["model"],
            temperature=config["temperature"],
            max_output_tokens=config["max_output_tokens"],
            project=project,
            location=config["location"],
            # Context caching pour Gemini est géré automatiquement
            # par Vertex AI pour les contextes > 32768 tokens
        )
    
    @classmethod
    def get_provider_info(cls, provider: ModelProvider) -> dict:
        """
        Retourne les informations sur un provider.
        
        Args:
            provider: Le provider de modèle
            
        Returns:
            Dict avec les infos du provider (model, pricing, etc.)
        """
        if provider == ModelProvider.CLAUDE:
            return {
                "name": "Claude Sonnet 4",
                "model": cls.CLAUDE_CONFIG["model"],
                "provider": "Anthropic",
                "pricing": {
                    "input": "$3.00 / 1M tokens",
                    "output": "$15.00 / 1M tokens",
                    "estimated_cost_per_search": "$0.069",
                },
                "features": [
                    "Raisonnement avancé",
                    "Compréhension nuancée",
                    "Excellent pour planification complexe",
                ],
            }
        elif provider == ModelProvider.GEMINI:
            return {
                "name": "Gemini 2.0 Flash",
                "model": cls.GEMINI_CONFIG["model"],
                "provider": "Google Vertex AI",
                "pricing": {
                    "input": "$0.075 / 1M tokens",
                    "output": "$0.30 / 1M tokens",
                    "estimated_cost_per_search": "$0.0016",
                },
                "features": [
                    "Très rapide",
                    "Coût 98% inférieur à Claude",
                    "Multimodal natif",
                    "Bon pour tâches répétitives",
                ],
            }
        else:
            raise ValueError(f"Provider non supporté: {provider}")
