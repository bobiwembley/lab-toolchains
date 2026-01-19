# Exemples d'intégration OpenTelemetry dans le Travel Agent

## 1. Instrumentation de l'agent principal

```python
# agents/travel_agent.py

from utils.telemetry import get_telemetry, init_telemetry
import time

class TravelAgent:
    def __init__(self, model_provider: ModelProvider, fast_mode: bool = False):
        # ... initialisation existante ...
        
        # Initialiser la télémétrie si pas déjà fait
        if not get_telemetry():
            init_telemetry(
                service_name="travel-agent",
                service_version="1.0.0",
                otlp_endpoint=os.getenv("OTLP_ENDPOINT", "localhost:4317")
            )
        
        self.telemetry = get_telemetry()
        logger.info("✅ OpenTelemetry instrumentation activée")
    
    def chat(self, user_input: str) -> str:
        """Chat avec instrumentation OpenTelemetry complète."""
        start_time = time.time()
        
        # Détection d'intent
        intent = self._detect_intent_semantic(user_input)
        use_light = (intent == 'small_talk')
        
        # Créer un span racine pour toute la conversation
        if self.telemetry:
            with self.telemetry.trace_agent_iteration(0) as root_span:
                root_span.set_attribute("agent.intent", intent)
                root_span.set_attribute("agent.fast_mode", self.fast_mode)
                root_span.set_attribute("agent.user_input_length", len(user_input))
                root_span.set_attribute("agent.model_provider", self.model_provider.value)
                
                try:
                    # Logique chat existante
                    response = self._execute_chat(user_input, intent, use_light)
                    
                    # Ajouter métriques de succès
                    latency_ms = (time.time() - start_time) * 1000
                    root_span.set_attribute("agent.latency_ms", latency_ms)
                    root_span.set_attribute("agent.response_length", len(response))
                    
                    # Enregistrer la latence dans les métriques
                    if hasattr(self.telemetry, 'latency_histogram'):
                        self.telemetry.latency_histogram.record(
                            latency_ms,
                            {"intent": intent, "fast_mode": str(self.fast_mode).lower()}
                        )
                    
                    return response
                    
                except Exception as e:
                    # Enregistrer l'exception dans le span
                    root_span.record_exception(e)
                    self.telemetry.record_error(type(e).__name__, "agent.chat")
                    raise
        else:
            # Fallback sans télémétrie
            return self._execute_chat(user_input, intent, use_light)
    
    def _execute_chat(self, user_input: str, intent: str, use_light: bool) -> str:
        """Logique chat existante (extraite pour clarté)."""
        # ... code existant du chat() ...
        
        # Créer le system message
        system_msg = self._create_system_message(use_light_prompt=use_light)
        
        # Préparer les messages
        messages = [system_msg] + self.history[-10:] + [HumanMessage(content=user_input)]
        
        # Invoquer l'agent avec instrumentation LLM
        if self.telemetry:
            with self.telemetry.trace_llm_call(
                model=self.model_name,
                provider=self.model_provider.value
            ) as llm_span:
                llm_span.set_attribute("llm.fast_mode", self.fast_mode)
                llm_span.set_attribute("llm.temperature", self.temperature)
                llm_span.set_attribute("llm.intent", intent)
                
                result = self.agent_executor.invoke(
                    {"messages": messages},
                    config={"max_iterations": max_iter, "recursion_limit": 100}
                )
        else:
            # Sans télémétrie
            result = self.agent_executor.invoke(
                {"messages": messages},
                config={"max_iterations": max_iter, "recursion_limit": 100}
            )
        
        # ... reste du traitement ...
        return response
```

## 2. Instrumentation des tools

```python
# tools/travel_tools.py

from utils.telemetry import get_telemetry
import time

def search_flights(departure: str, arrival: str, date: str) -> str:
    """Recherche de vols avec instrumentation."""
    telemetry = get_telemetry()
    
    if telemetry:
        with telemetry.trace_tool_call("search_flights") as span:
            span.set_attribute("tool.departure", departure)
            span.set_attribute("tool.arrival", arrival)
            span.set_attribute("tool.date", date)
            
            start_time = time.time()
            
            try:
                # Appel API Amadeus existant
                result = _amadeus_flight_search(departure, arrival, date)
                
                # Métriques de succès
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("tool.latency_ms", latency_ms)
                span.set_attribute("tool.result_count", len(result))
                span.set_attribute("tool.success", True)
                
                return result
                
            except Exception as e:
                # Erreur tracée
                span.record_exception(e)
                span.set_attribute("tool.success", False)
                telemetry.record_error(type(e).__name__, "tool.search_flights")
                
                # Fallback mock
                logger.warning(f"Amadeus API error: {e}, using mock data")
                return _mock_flight_data()
    else:
        # Sans télémétrie (fallback)
        return _amadeus_flight_search(departure, arrival, date)


def search_hotels(city: str, check_in: str, check_out: str) -> str:
    """Recherche d'hôtels avec instrumentation."""
    telemetry = get_telemetry()
    
    if telemetry:
        with telemetry.trace_tool_call("search_hotels") as span:
            span.set_attribute("tool.city", city)
            span.set_attribute("tool.check_in", check_in)
            span.set_attribute("tool.check_out", check_out)
            
            try:
                result = _booking_hotel_search(city, check_in, check_out)
                span.set_attribute("tool.result_count", len(result))
                return result
                
            except Exception as e:
                span.record_exception(e)
                telemetry.record_error(type(e).__name__, "tool.search_hotels")
                return _mock_hotel_data()
    else:
        return _booking_hotel_search(city, check_in, check_out)


def get_airport_code(city: str) -> str:
    """Récupération code aéroport avec instrumentation."""
    telemetry = get_telemetry()
    
    if telemetry:
        with telemetry.trace_tool_call("get_airport_code") as span:
            span.set_attribute("tool.city", city)
            
            try:
                result = _get_airport_code_from_service(city)
                span.set_attribute("tool.airport_code", result)
                return result
                
            except Exception as e:
                span.record_exception(e)
                telemetry.record_error(type(e).__name__, "tool.get_airport_code")
                raise
    else:
        return _get_airport_code_from_service(city)
```

## 3. Intégration dans Streamlit

```python
# streamlit_app.py

import streamlit as st
from utils.telemetry import init_telemetry, get_telemetry
from agents.travel_agent import TravelAgent
import os

# Initialiser OpenTelemetry AU DÉMARRAGE (une seule fois)
if "telemetry_initialized" not in st.session_state:
    # Initialiser avec config depuis .env
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "localhost:4317")
    enable_console = os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true"
    
    init_telemetry(
        service_name="travel-agent",
        service_version="1.0.0",
        otlp_endpoint=otlp_endpoint,
        enable_console_export=enable_console
    )
    
    st.session_state.telemetry_initialized = True
    st.sidebar.success("✅ OpenTelemetry activé")

# Interface Streamlit existante
st.title("🌍 Agent de Voyage Multi-LLM")

# ... reste du code Streamlit ...

# Dans le traitement du message utilisateur
if prompt := st.chat_input("Votre message"):
    # Afficher le message utilisateur
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Obtenir la réponse de l'agent (déjà instrumenté)
    with st.spinner("🤔 Réflexion en cours..."):
        try:
            response = agent.chat(prompt)
            
            # Afficher la réponse
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"❌ Erreur: {e}")
            
            # L'erreur est déjà tracée dans agent.chat()
            telemetry = get_telemetry()
            if telemetry:
                telemetry.record_error(type(e).__name__, "streamlit.chat_input")
```

## 4. Corrélation logs avec traces

```python
# utils/logger.py

import structlog
from opentelemetry import trace

class ContextLogger:
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def _add_trace_context(self, kwargs: dict) -> dict:
        """Ajoute le contexte de trace aux logs."""
        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            kwargs['trace_id'] = format(ctx.trace_id, '032x')
            kwargs['span_id'] = format(ctx.span_id, '016x')
            kwargs['trace_flags'] = ctx.trace_flags
        return kwargs
    
    def info(self, message: str, **kwargs):
        """Log info avec trace_id."""
        kwargs = self._add_trace_context(kwargs)
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning avec trace_id."""
        kwargs = self._add_trace_context(kwargs)
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error avec trace_id."""
        kwargs = self._add_trace_context(kwargs)
        self.logger.error(message, **kwargs)

# Usage
logger = ContextLogger(__name__)

# Les logs auront maintenant trace_id et span_id automatiquement
logger.info("Chat message received", intent="planning", user_input_length=50)
# Output: {..., "trace_id": "abc123...", "span_id": "def456...", ...}
```

## 5. Monitoring du prompt caching

```python
# agents/travel_agent.py

def _create_system_message(self, use_light_prompt: bool = False) -> SystemMessage:
    """System message avec métriques de caching."""
    if use_light_prompt:
        prompt = self.SYSTEM_PROMPT_LIGHT
        prompt_type = "light"
    elif self.fast_mode:
        prompt = self.SYSTEM_PROMPT_FAST
        prompt_type = "fast"
    else:
        prompt = self.SYSTEM_PROMPT
        prompt_type = "full"
    
    # Ajouter au span actuel
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute("agent.prompt_type", prompt_type)
        span.set_attribute("agent.prompt_cached", True)  # Claude cache toujours
    
    # Claude avec cache control
    if self.model_provider == ModelProvider.CLAUDE:
        return SystemMessage(
            content=prompt,
            additional_kwargs={"cache_control": {"type": "ephemeral"}}
        )
    
    # Gemini (caching automatique)
    return SystemMessage(content=prompt)
```

## 6. Métriques custom de coût

```python
# agents/travel_agent.py

class TravelAgent:
    def __init__(self, ...):
        # ... init existant ...
        self._total_cost = 0.0
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int, cached: bool) -> float:
        """Estime le coût d'un appel LLM."""
        if self.model_provider == ModelProvider.CLAUDE:
            # Claude Sonnet 4: $3/$15 per 1M tokens
            prompt_cost = (prompt_tokens / 1_000_000) * 3.0
            completion_cost = (completion_tokens / 1_000_000) * 15.0
            
            # -90% sur prompt si caché
            if cached:
                prompt_cost *= 0.1
            
            return prompt_cost + completion_cost
        
        elif self.model_provider == ModelProvider.GEMINI:
            # Gemini 2.0 Flash: gratuit jusqu'à 2M RPM
            return 0.0
        
        return 0.0
    
    def chat(self, user_input: str) -> str:
        # ... dans le code existant, après l'invoke ...
        
        # Estimer le coût (si disponible via response metadata)
        if hasattr(result, 'usage_metadata'):
            usage = result.usage_metadata
            cost = self._estimate_cost(
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                cached=getattr(usage, 'cache_read_input_tokens', 0) > 0
            )
            
            # Mettre à jour le coût total
            self._total_cost += cost
            
            # Enregistrer dans la télémétrie
            if self.telemetry:
                self.telemetry.update_cost(cost)
                
                # Enregistrer les tokens
                self.telemetry.record_llm_metrics(
                    model=self.model_name,
                    prompt_tokens=usage.input_tokens,
                    completion_tokens=usage.output_tokens,
                    cached=getattr(usage, 'cache_read_input_tokens', 0) > 0
                )
            
            # Logger le coût
            logger.info(
                "💰 LLM call cost estimated",
                model=self.model_name,
                cost_usd=round(cost, 6),
                total_cost_usd=round(self._total_cost, 6),
                cached=getattr(usage, 'cache_read_input_tokens', 0) > 0
            )
```

## 7. Dashboard Grafana example queries

### Panel: Requests par seconde
```promql
sum(rate(agent_requests_total[5m])) by (intent)
```

### Panel: Latence P95 par intent
```promql
histogram_quantile(0.95, 
  sum(rate(agent_request_duration_bucket[5m])) by (intent, le)
)
```

### Panel: Taux d'erreur
```promql
sum(rate(agent_errors_total[5m])) by (error_type) / 
sum(rate(agent_requests_total[5m]))
```

### Panel: Coût LLM cumulé
```promql
sum(agent_llm_estimated_cost)
```

### Panel: Cache hit rate (Claude)
```promql
sum(rate(agent_llm_tokens{llm_cached="true"}[5m])) /
sum(rate(agent_llm_tokens{token_type="prompt"}[5m]))
```

### Panel: Tool success rate
```promql
sum(rate(agent_tool_calls{tool_success="true"}[5m])) by (tool_name) /
sum(rate(agent_tool_calls[5m])) by (tool_name)
```

---

**Note**: Tous ces exemples sont prêts à intégrer. La structure d'instrumentation est déjà en place dans `utils/telemetry.py`, il suffit d'ajouter les appels aux bons endroits.
