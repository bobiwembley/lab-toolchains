"""
Professional Travel Agent - Core agent logic
Implements LangChain agent with tools
Support multi-modèles: Claude (Anthropic) et Gemini (Vertex AI)
"""

import os
import time
from typing import Optional, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
import langchain
from typing import Dict, Any

from agents.model_factory import ModelFactory, ModelProvider
from utils.logger import ContextLogger, llm_latency, agent_iterations
from utils.telemetry import get_telemetry

# Désactiver le logging verbeux de LangChain (on utilise notre système)
langchain.debug = False
langchain.verbose = False

logger = ContextLogger(__name__)
load_dotenv()


class TravelAgent:
    """
    Production-ready travel agent with multi-model support (Claude + Gemini)
    Modular design following LangChain patterns
    """
    
    # Prompt optimisé avec détection d'intention (-70% outils pour small talk)
    SYSTEM_PROMPT = """Professional travel agent with intelligent intent detection.

INTENT DETECTION (CRITICAL):
1. SMALL TALK (greetings, how are you, thanks, goodbye)
   → Respond naturally, NO TOOLS, be friendly
   Examples: "Bonjour!", "Comment vas-tu?", "Merci", "Au revoir"
   
2. INFORMATION REQUEST (single city/destination mentioned)
   → Ask clarifying questions BEFORE using tools
   Examples: "Nice" → Ask: dates? budget? interests?
   "Tokyo" → Ask: when? how long? what type of trip?
   
3. CONFIRMATION / GO AHEAD (user confirms with "go", "fais le", "lance", "ok go")
   → EXTRACT info from conversation history and LAUNCH TOOLS IMMEDIATELY
   → Look for: destination, dates, budget, travelers in previous messages
   → DO NOT ask more questions, START PLANNING NOW
   
4. TRAVEL PLANNING (clear destination + details)
   → Use tools in parallel, create comprehensive plan
   Examples: "Je veux aller à Tokyo en avril", "Un voyage à Nice budget 2000€"

CORE RULES:
- NO TOOLS for greetings/small talk
- ASK QUESTIONS when missing info (ONCE only)
- When user confirms → EXTRACT from history + LAUNCH TOOLS IMMEDIATELY
- Use tools IN PARALLEL when ready (airport + flights + hotels + activities)
- ALWAYS provide detailed recommendations with specific options

DEFAULTS (when planning):
Origin: Paris (CDG) | Dates: +2 months, 7 days | Travelers: 2 | Budget: $$

WORKFLOW (when planning confirmed):
1. Extract: destination, dates, budget, travelers from conversation
2. Parallel: get_airport_code + search_flights + search_hotels
3. Parallel: find_cultural_activities + find_restaurants
4. RESPOND with detailed plan: flights (with prices), hotels (3 options), activities (top 5), budget summary

FORMAT: Friendly → Specific → Actionable (ALWAYS include prices and booking details)"""
    
    # Prompt pour mode rapide (sans activités/restaurants)
    SYSTEM_PROMPT_FAST = """Professional travel agent - FAST MODE (essentials only).

INTENT DETECTION (CRITICAL):
1. SMALL TALK → Respond naturally, NO TOOLS
2. INFORMATION REQUEST → Ask clarifying questions
3. CONFIRMATION → EXTRACT from history + LAUNCH TOOLS IMMEDIATELY
4. TRAVEL PLANNING → Use available tools in parallel

AVAILABLE TOOLS (FAST MODE):
- get_airport_code: Find airport codes
- search_flights: Find flight options with prices
- search_hotels: Find hotel accommodations
- calculate_total_cost: Calculate budget breakdown
- recommend_best_package: Package recommendations

CORE RULES:
- NO TOOLS for small talk
- ASK QUESTIONS when missing info (ONCE only)
- When user confirms → EXTRACT from history + LAUNCH TOOLS
- Use tools IN PARALLEL when ready (airport + flights + hotels)
- Focus on flights & hotels (no activities/restaurants available in fast mode)

DEFAULTS: Origin: Paris (CDG) | Dates: +2 months, 7 days | Travelers: 2 | Budget: $$

WORKFLOW (when planning confirmed):
1. Extract: destination, dates, budget, travelers from conversation
2. Parallel: get_airport_code + search_flights + search_hotels
3. Calculate: calculate_total_cost with results
4. RESPOND: flights (with prices), hotels (3 options), cost breakdown

FORMAT: Friendly → Specific → Actionable (ALWAYS include prices)"""
    
    # Prompt léger pour small talk (économise tokens et latence)
    SYSTEM_PROMPT_LIGHT = """Friendly travel agent assistant.

You help users plan trips. For now, just have a natural conversation.
If user mentions a destination, ask clarifying questions (dates, budget, interests).
DO NOT use any tools until you have enough information for a complete trip plan.

Be warm, professional, and helpful."""
    
    def _detect_intent(self, user_input: str) -> str:
        """Détecte l'intention avec compréhension sémantique via LLM.
        
        Returns:
            'small_talk': Salutations, remerciements, questions générales
            'confirmation': Confirmation/validation pour lancer la planification
            'planning': Demande concrète de planification de voyage
        """
        # Prompt ultra-léger pour classification d'intention
        intent_prompt = f"""Classifie l'intention du message utilisateur en UNE catégorie:

CATEGORIES:
- small_talk: salutations, remerciements, questions générales, conversation sociale
- confirmation: confirmation explicite pour lancer une action ("fais le", "go", "lance", "ok vas-y", "c'est bon")
- planning: demande de planification voyage, informations destination/dates/budget

MESSAGE: "{user_input}"

REPONDS UNIQUEMENT PAR: small_talk, confirmation ou planning"""

        try:
            # Utiliser le modèle déjà configuré (léger et rapide)
            # On réutilise self.llm pour économiser les coûts et simplifier
            response = self.llm.invoke(intent_prompt)
            intent = response.content.strip().lower()
            
            # Validation et fallback
            valid_intents = ['small_talk', 'confirmation', 'planning']
            if intent in valid_intents:
                return intent
            
            # Si le LLM répond avec plus de texte, extraire
            for valid in valid_intents:
                if valid in intent:
                    return valid
            
            # Fallback: planning par défaut
            return 'planning'
            
        except Exception as e:
            logger.warning(f"⚠️ Semantic intent detection failed: {e}, using keyword fallback")
            
            # Fallback sur pattern matching simple
            user_lower = user_input.lower().strip()
            
            # Small talk basique
            if any(word in user_lower for word in ['bonjour', 'hello', 'merci', 'salut', 'hi']):
                if len(user_input) < 50:
                    return 'small_talk'
            
            # Confirmation basique
            if any(word in user_lower for word in ['fais le', 'go', 'lance', 'ok', 'vas-y', 'c\'est bon']):
                if len(user_input) < 30:
                    return 'confirmation'
            
            return 'planning'
    
    def _create_system_message(self, use_light_prompt: bool = False) -> SystemMessage:
        """Crée un SystemMessage avec prompt caching activé pour Claude.
        
        Args:
            use_light_prompt: Si True, utilise le prompt léger pour small talk
        """
        # Choisir le prompt selon le contexte
        if use_light_prompt:
            prompt = self.SYSTEM_PROMPT_LIGHT
        elif self.fast_mode:
            prompt = self.SYSTEM_PROMPT_FAST  # Prompt adapté au mode rapide
        else:
            prompt = self.SYSTEM_PROMPT  # Prompt complet avec tous les outils
        
        # Pour Claude: ajouter cache_control pour mettre en cache le prompt système
        # Cela réduit les coûts de 90% et la latence pour les messages répétés
        if self.model_provider == ModelProvider.CLAUDE:
            return SystemMessage(
                content=prompt,
                additional_kwargs={
                    "cache_control": {"type": "ephemeral"}
                }
            )
        else:
            # Pour Gemini, le caching est géré automatiquement par le modèle
            return SystemMessage(content=prompt)
    
    def __init__(
        self,
        tools: List[BaseTool],
        model_provider: ModelProvider = ModelProvider.CLAUDE,
        api_key: Optional[str] = None,
        temperature: float = 0.3,  # Réduit de 0.5 → 0.3 pour réponses plus rapides
        fast_mode: bool = False  # Mode rapide: moins d'outils, réponse plus rapide
    ):
        """
        Initialize travel agent with model provider choice
        
        Args:
            tools: List of LangChain tools
            model_provider: ModelProvider.CLAUDE or ModelProvider.GEMINI
            api_key: API key (for Claude only, uses env var if not provided)
            temperature: Model temperature (0-1). Lower = faster, more deterministic
            fast_mode: If True, uses only essential tools (5 vs 12) for faster response
        """
        self.model_provider = model_provider
        self.fast_mode = fast_mode
        self.telemetry = get_telemetry()  # Initialiser OpenTelemetry
        
        # Debug: vérifier si telemetry est initialisé
        if self.telemetry:
            logger.info("✅ Telemetry enabled for agent", telemetry_active=True)
        else:
            logger.warning("⚠️ Telemetry is None - traces will not be created", telemetry_active=False)
        
        # En mode rapide, utiliser seulement les outils essentiels
        if fast_mode:
            essential_tool_names = [
                'get_airport_code',
                'search_flights',
                'search_hotels',
                'calculate_total_cost',
                'recommend_best_package'
            ]
            self.tools = [t for t in tools if t.name in essential_tool_names]
            logger.info("⚡ Fast mode enabled", tools_count=len(self.tools))
        else:
            self.tools = tools
            
        self.chat_history = []  # Historique des conversations pour le mode chatbot
        
        # Créer le LLM via la factory
        logger.info(f"🚀 Initializing TravelAgent with {model_provider.value}...")
        
        try:
            if model_provider == ModelProvider.CLAUDE:
                # Pour Claude, on peut override l'API key
                if api_key:
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                
                self.llm = ModelFactory.create_llm(
                    provider=ModelProvider.CLAUDE,
                    temperature=temperature,
                    max_tokens=3072
                )
            else:  # GEMINI
                self.llm = ModelFactory.create_llm(
                    provider=ModelProvider.GEMINI,
                    temperature=temperature,
                    max_tokens=3072
                )
            
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            
            provider_info = ModelFactory.get_provider_info(model_provider)
            logger.info(
                f"✅ TravelAgent initialized with {provider_info['name']}",
                model=provider_info['model'],
                model_provider=model_provider.value,
                cost_per_search=provider_info['pricing']['estimated_cost_per_search'],
                tools_count=len(tools)
            )
            
        except Exception as e:
            logger.error(
                f"❌ Failed to initialize {model_provider.value}",
                model_provider=model_provider.value,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def plan_trip(self, user_request: str) -> str:
        """
        Plan a trip based on natural language request
        
        Args:
            user_request: User's travel request in natural language
            
        Returns:
            Personalized travel recommendations
        """
        messages = [
            self._create_system_message(),
            HumanMessage(content=user_request)
        ]
        
        start_time = time.time()
        
        try:
            logger.set_context(user_request=user_request[:100])  # Tronquer pour logs
            logger.info("🤖 Analyzing request")
            
            # Boucle pour permettre plusieurs cycles d'outils
            # Fast mode: 5 iterations (3-4 outils + réponse finale)
            # Full mode: 8 iterations (recherches plus complexes)
            max_iterations = 5 if self.fast_mode else 8
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                agent_iterations.set(iteration)
                
                # Invocation LLM avec timing
                llm_start = time.time()
                response = self.llm_with_tools.invoke(messages)
                llm_duration = time.time() - llm_start
                
                # Log métriques LLM
                llm_latency.labels(model=self.model_provider.value).observe(llm_duration)
                
                # Si pas d'outils à lancer, on retourne la réponse
                if not response.tool_calls:
                    total_duration = time.time() - start_time
                    logger.info(
                        f"✅ Finished after {iteration} iteration(s)",
                        iterations=iteration,
                        total_duration_seconds=total_duration
                    )
                    logger.clear_context()
                    return response.content
                
                logger.log_agent_iteration(
                    iteration=iteration,
                    tools_used=[tc['name'] for tc in response.tool_calls],
                    llm_duration_seconds=llm_duration
                )
                
                # Add Claude's response with tool calls
                messages.append(response)
                
                # Execute each tool
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    # Find and execute tool avec timing
                    tool_func = next((t for t in self.tools if t.name == tool_name), None)
                    
                    if tool_func:
                        tool_start = time.time()
                        result = tool_func.invoke(tool_args)
                        tool_duration = time.time() - tool_start
                        
                        logger.info(
                            f"   → Tool executed: {tool_name}",
                            tool_name=tool_name,
                            tool_args=tool_args,
                            tool_duration_seconds=tool_duration,
                            result_length=len(str(result))
                        )
                        
                        # Add tool result with correct ID
                        messages.append(ToolMessage(
                            content=result,
                            tool_call_id=tool_id
                        ))
                    else:
                        logger.warning(
                            f"   ⚠️  Unknown tool: {tool_name}",
                            tool_name=tool_name,
                            available_tools=[t.name for t in self.tools]
                        )
            
            # Si on arrive ici, on a atteint max_iterations
            logger.info("📊 Generating final response...")
            final_response = self.llm.invoke(messages)
            
            total_duration = time.time() - start_time
            logger.info(
                "✅ Request completed",
                max_iterations_reached=True,
                total_duration_seconds=total_duration
            )
            logger.clear_context()
            
            return final_response.content
            
        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(
                "❌ Agent execution failed",
                error=str(e),
                error_type=type(e).__name__,
                total_duration_seconds=total_duration,
                exc_info=True
            )
            logger.clear_context()
            raise
    
    def chat(self, user_input: str) -> str:
        """
        Chat avec l'agent en mode conversationnel interactif.
        Maintient l'historique des messages pour permettre un contexte continu.
        Détecte automatiquement l'intention pour optimiser le contexte.
        Instrumenté avec OpenTelemetry pour observabilité complète.
        
        Args:
            user_input: Message de l'utilisateur
            
        Returns:
            Réponse de l'agent
        """
        # Détecter l'intention pour optimiser le contexte
        intent = self._detect_intent(user_input)
        use_light_prompt = (intent == 'small_talk')
        
        # Logging avec emoji selon l'intention
        intent_icons = {
            'small_talk': '💬',
            'confirmation': '✅',
            'planning': '🗺️'
        }
        icon = intent_icons.get(intent, '🗺️')
        
        if use_light_prompt:
            logger.info(f"{icon} Small talk detected - using light context", intent=intent)
        else:
            logger.info(f"{icon} {intent.capitalize()} intent detected - full context", intent=intent)
        
        # Ajouter le message utilisateur à l'historique
        self.chat_history.append(HumanMessage(content=user_input))
        
        # Pruning: garder seulement les 10 derniers messages (5 échanges)
        # Évite la surcharge de contexte sur longues conversations
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]
            logger.info("🔄 History pruned to last 10 messages", history_length=10)
        
        # Préparer les messages: System Prompt (avec caching) + Historique complet
        # Utilise le prompt léger pour small talk, complet pour planification
        messages = [self._create_system_message(use_light_prompt=use_light_prompt)] + self.chat_history
        
        start_time = time.time()
        
        try:
            logger.set_context(user_input=user_input[:100])
            logger.info("💬 Chat message received", history_length=len(self.chat_history))
            
            # Boucle d'itération de l'agent
            # Fast mode: 5 iterations (permet 3-4 outils + réponse finale)
            # Full mode: 8 iterations (recherches plus complexes)
            max_iterations = 5 if self.fast_mode else 8
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                agent_iterations.set(iteration)
                
                # Invocation LLM avec timing
                llm_start = time.time()
                response = self.llm_with_tools.invoke(messages)
                llm_duration = time.time() - llm_start
                
                # Log métriques LLM
                llm_latency.labels(model=self.model_provider.value).observe(llm_duration)
                
                # Si pas d'outils à lancer, on a la réponse finale
                if not response.tool_calls:
                    total_duration = time.time() - start_time
                    logger.info(
                        f"✅ Chat response ready after {iteration} iteration(s)",
                        iterations=iteration,
                        total_duration_seconds=total_duration
                    )
                    
                    # Ajouter la réponse de l'agent à l'historique
                    self.chat_history.append(response)
                    logger.clear_context()
                    
                    return response.content
                
                logger.log_agent_iteration(
                    iteration=iteration,
                    tools_used=[tc['name'] for tc in response.tool_calls],
                    llm_duration_seconds=llm_duration
                )
                
                # Ajouter la réponse avec les tool calls
                messages.append(response)
                
                # Exécuter chaque outil
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']
                    
                    # Trouver et exécuter l'outil
                    tool_func = next((t for t in self.tools if t.name == tool_name), None)
                    
                    if tool_func:
                        tool_start = time.time()
                        result = tool_func.invoke(tool_args)
                        tool_duration = time.time() - tool_start
                        
                        logger.info(
                            f"   → Tool executed: {tool_name}",
                            tool_name=tool_name,
                            tool_args=tool_args,
                            tool_duration_seconds=tool_duration,
                            result_length=len(str(result))
                        )
                        
                        # Ajouter le résultat de l'outil
                        messages.append(ToolMessage(
                            content=result,
                            tool_call_id=tool_id
                        ))
                    else:
                        logger.warning(
                            f"   ⚠️  Unknown tool: {tool_name}",
                            tool_name=tool_name,
                            available_tools=[t.name for t in self.tools]
                        )
            
            # Si on atteint max_iterations, générer une réponse finale
            logger.info("📊 Generating final chat response...")
            final_response = self.llm.invoke(messages)
            
            total_duration = time.time() - start_time
            total_duration_ms = round(total_duration * 1000, 2)
            
            logger.info(
                "✅ Chat completed (max iterations reached)",
                max_iterations_reached=True,
                total_duration_seconds=total_duration
            )
            
            # Enregistrer les métriques de télémétrie
            if self.telemetry:
                # Enregistrer la latence dans les métriques
                self.telemetry.record_latency(total_duration_ms, intent)
            
            # Ajouter la réponse finale à l'historique
            self.chat_history.append(final_response)
            logger.clear_context()
            
            return final_response.content
            
        except Exception as e:
            total_duration = time.time() - start_time
            
            # Enregistrer l'erreur
            if self.telemetry:
                self.telemetry.record_error(type(e).__name__, "agent.chat")
            
            logger.error(
                "❌ Chat execution failed",
                error=str(e),
                error_type=type(e).__name__,
                total_duration_seconds=total_duration,
                exc_info=True
            )
            logger.clear_context()
            raise
    
    def reset_conversation(self):
        """
        Réinitialise l'historique de conversation.
        Utile pour démarrer une nouvelle conversation ou gérer plusieurs utilisateurs.
        """
        self.chat_history = []
        logger.info("🔄 Conversation history reset")
    
    def get_conversation_length(self) -> int:
        """
        Retourne le nombre de messages dans l'historique.
        Utile pour implémenter le pruning ou la gestion de la fenêtre de contexte.
        
        Returns:
            Nombre de messages dans l'historique
        """
        return len(self.chat_history)
