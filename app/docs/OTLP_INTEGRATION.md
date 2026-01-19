# Guide d'intégration OpenTelemetry

Ce guide décrit l'intégration de l'instrumentation OpenTelemetry (OTLP) avec la stack Grafana pour le Travel Agent.

## Architecture

```
Travel Agent (Python)
    ↓ OTLP gRPC (port 4317)
OpenTelemetry Collector
    ↓ Traces → Tempo
    ↓ Metrics → Prometheus
    ↓ Logs → Loki
    ↓
Grafana (visualisation)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Grafana Stack

```bash
docker-compose -f docker-compose.observability.yml up -d
```

Services disponibles:
- **Grafana**: http://localhost:3000 (datasources pre-configured)
- **Tempo**: http://localhost:3200 (traces)
- **Loki**: http://localhost:3100 (logs)
- **Prometheus**: http://localhost:9090 (métriques)
- **OTLP Collector**: localhost:4317 (endpoint gRPC)

### 3. Intégration dans le Travel Agent

#### Option A: Instrumentation automatique

```python
# Dans streamlit_app.py ou au démarrage
from utils.telemetry import init_telemetry

# Initialiser la télémétrie
telemetry = init_telemetry(
    service_name="travel-agent",
    service_version="1.0.0",
    otlp_endpoint="localhost:4317",
    enable_console_export=False  # True pour debug
)
```

#### Option B: Instrumentation manuelle dans l'agent

```python
# Dans agents/travel_agent.py
from utils.telemetry import get_telemetry
import time

class TravelAgent:
    def __init__(self, ...):
        # ... code existant
        self.telemetry = get_telemetry()
    
    def chat(self, user_input: str) -> str:
        """Chat avec instrumentation OpenTelemetry."""
        start_time = time.time()
        intent = self._detect_intent_semantic(user_input)
        
        # Créer un span racine pour la requête complète
        with self.telemetry.trace_agent_iteration(0) as span:
            span.set_attribute("agent.intent", intent)
            span.set_attribute("agent.user_input_length", len(user_input))
            
            try:
                # ... logique chat existante
                
                # Instrumenter les appels LLM
                with self.telemetry.trace_llm_call(
                    model=self.model_name,
                    provider=self.model_provider.value
                ) as llm_span:
                    response = self.agent_executor.invoke(...)
                    llm_span.set_attribute("llm.response_length", len(response))
                
                # Enregistrer la latence
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("agent.latency_ms", latency_ms)
                
                return response
                
            except Exception as e:
                span.record_exception(e)
                self.telemetry.record_error(type(e).__name__, "agent.chat")
                raise
```

#### Instrumentation des tools

```python
# Dans tools/travel_tools.py
from utils.telemetry import get_telemetry

def search_flights(departure: str, arrival: str, date: str) -> str:
    """Recherche de vols avec télémétrie."""
    telemetry = get_telemetry()
    
    if telemetry:
        with telemetry.trace_tool_call("search_flights") as span:
            span.set_attribute("tool.departure", departure)
            span.set_attribute("tool.arrival", arrival)
            span.set_attribute("tool.date", date)
            
            # Appel API existant
            result = _do_flight_search(departure, arrival, date)
            
            span.set_attribute("tool.result_count", len(result))
            return result
    else:
        # Fallback sans télémétrie
        return _do_flight_search(departure, arrival, date)
```

## Configuration avancée

### Variables d'environnement

Créer un fichier `.env`:

```bash
# OpenTelemetry
OTLP_ENDPOINT=localhost:4317
SERVICE_NAME=travel-agent
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
OTEL_CONSOLE_EXPORT=false  # true pour debug
```

### Filtrage des spans (production)

Pour réduire le volume en production, configurer le sampling dans `otel-collector/config.yaml`:

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 10  # 10% des traces

service:
  pipelines:
    traces:
      processors: [probabilistic_sampler, batch, resource]
```

### Corrélation logs ↔ traces

Les logs existants (JSON) peuvent être corrélés avec les traces:

```python
# Dans utils/logger.py
from opentelemetry import trace

class ContextLogger:
    def info(self, message: str, **kwargs):
        # Ajouter trace_id aux logs
        span = trace.get_current_span()
        if span.is_recording():
            kwargs['trace_id'] = format(span.get_span_context().trace_id, '032x')
            kwargs['span_id'] = format(span.get_span_context().span_id, '016x')
        
        self.logger.info(message, extra=kwargs)
```

Configuration Grafana Loki pour extraire `trace_id` → voir dans `grafana/provisioning/datasources/datasources.yaml`.

## Métriques disponibles

### LLM Metrics
- `agent.llm.calls` - Compteur d'appels LLM (par modèle, provider)
- `agent.llm.latency` - Histogramme latence LLM (ms)
- `agent.llm.tokens` - Compteur de tokens (prompt, completion, total)

### Tool Metrics
- `agent.tool.calls` - Compteur d'appels tools (par tool, success)
- `agent.tool.latency` - Histogramme latence tools (ms)

### Agent Metrics
- `agent.iterations` - Compteur d'itérations agent
- `agent.requests.total` - Compteur de requêtes (par intent)
- `agent.request.duration` - Histogramme durée requête (ms)
- `agent.errors.total` - Compteur d'erreurs (par type)

### Coût
- `agent.llm.estimated_cost` - Gauge du coût estimé (USD)

## Dashboards Grafana

### Importer les dashboards

1. Ouvrir Grafana: http://localhost:3000
2. Menu: Dashboards → Import
3. Importer les templates suivants:

#### Dashboard Agent Performance
```json
{
  "title": "Travel Agent Performance",
  "panels": [
    {
      "title": "Requests by Intent",
      "targets": [
        {
          "expr": "rate(agent_requests_total[5m])",
          "legendFormat": "{{intent}}"
        }
      ]
    },
    {
      "title": "Request Latency (P95)",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(agent_request_duration_bucket[5m]))"
        }
      ]
    }
  ]
}
```

#### Dashboard LLM Cost
```json
{
  "title": "LLM Cost Monitoring",
  "panels": [
    {
      "title": "Token Consumption",
      "targets": [
        {
          "expr": "rate(agent_llm_tokens[5m])",
          "legendFormat": "{{llm_model}} - {{token_type}}"
        }
      ]
    },
    {
      "title": "Estimated Cost (USD)",
      "targets": [
        {
          "expr": "agent_llm_estimated_cost"
        }
      ]
    }
  ]
}
```

### Exploration des traces

1. Grafana → Explore
2. Datasource: **Tempo**
3. Query: `{service.name="travel-agent"}`
4. Filtrer par:
   - `agent.intent="planning"`
   - `llm.model="claude-sonnet-4"`
   - `tool.name="search_flights"`

### Logs corrélés

1. Grafana → Explore
2. Datasource: **Loki**
3. Query: `{service_name="travel-agent"} | json`
4. Cliquer sur `trace_id` dans un log → voir la trace complète dans Tempo

## Exemples de requêtes

### Prometheus (métriques)

```promql
# Taux de requêtes par intent (dernières 5 minutes)
rate(agent_requests_total[5m])

# Latence P95 par intent
histogram_quantile(0.95, rate(agent_request_duration_bucket[5m]))

# Taux d'erreurs
rate(agent_errors_total[5m])

# Tokens consommés par modèle
sum by (llm_model) (rate(agent_llm_tokens[5m]))

# Coût estimé cumulé
sum(agent_llm_estimated_cost)
```

### Loki (logs)

```logql
# Logs d'erreur avec trace_id
{service_name="travel-agent"} |= "ERROR" | json | trace_id != ""

# Logs de confirmation workflow
{service_name="travel-agent"} |= "Confirmation intent detected" | json

# Latence des requêtes > 5 secondes
{service_name="travel-agent"} | json | duration_ms > 5000
```

### Tempo (traces)

```
# Toutes les traces du service
{service.name="travel-agent"}

# Traces avec intent=planning
{service.name="travel-agent" && agent.intent="planning"}

# Traces avec erreurs
{service.name="travel-agent" && status=error}

# Traces lentes (> 3s)
{service.name="travel-agent" && duration>3s}
```

## Troubleshooting

### Les traces n'apparaissent pas dans Tempo

1. Vérifier que l'OpenTelemetry Collector est lancé:
   ```bash
   docker-compose -f docker-compose.observability.yml ps
   ```

2. Vérifier les logs du collector:
   ```bash
   docker-compose -f docker-compose.observability.yml logs otel-collector
   ```

3. Tester l'endpoint OTLP:
   ```bash
   telnet localhost 4317
   ```

4. Activer le debug dans l'agent:
   ```python
   telemetry = init_telemetry(enable_console_export=True)
   ```

### Les métriques ne remontent pas

1. Vérifier le scraping Prometheus:
   http://localhost:9090/targets

2. Vérifier que le collector exporte bien:
   http://localhost:8889/metrics

### Corrélation logs/traces ne fonctionne pas

1. Vérifier que `trace_id` est bien dans les logs JSON
2. Vérifier la configuration Loki dans Grafana:
   - Derived fields configured
   - Regex: `trace_id=(\w+)`

## Performance et volumétrie

### Overhead estimé

- **Traces**: ~1-2% CPU overhead, ~100Ko/requête
- **Métriques**: ~0.5% CPU overhead, agrégées toutes les 15s
- **Logs**: Négligeable (déjà en place)

### Retention

- **Tempo**: 1h (configurable dans tempo.yaml)
- **Loki**: Défaut (configurable)
- **Prometheus**: 15 jours (configurable dans prometheus.yml)

### En production

Ajuster le sampling pour réduire le volume:
- Traces: 10% (head-based sampling)
- Métriques: Export toutes les 60s au lieu de 15s
- Logs: Filtrer les niveaux DEBUG/INFO

## Ressources

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [Grafana Loki](https://grafana.com/docs/loki/latest/)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)

---

**Auteur**: Ingénieur Observabilité  
**Date**: 2026-01-19  
**Version**: 1.0.0
