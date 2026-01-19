# Checklist d'implémentation OTLP

## ✅ Infrastructure (Complété)

- [x] Docker Compose pour stack Grafana
  - [x] Grafana (port 3000)
  - [x] Tempo (traces, port 3200)
  - [x] Loki (logs, port 3100)
  - [x] Prometheus (métriques, port 9090)
  - [x] OpenTelemetry Collector (OTLP, port 4317)

- [x] Configuration Tempo (tempo/tempo.yaml)
- [x] Configuration Prometheus (prometheus/prometheus.yml)
- [x] Configuration OpenTelemetry Collector (otel-collector/config.yaml)
- [x] Datasources Grafana auto-provisionnées
- [x] Script de démarrage (start-observability.sh)

## ✅ Code (Prêt à intégrer)

- [x] Module telemetry.py complet avec:
  - [x] TracerProvider (traces)
  - [x] MeterProvider (métriques)
  - [x] Context managers (spans)
  - [x] Métriques custom (LLM, tools, agent)
  - [x] Gestion des erreurs

- [x] Dépendances ajoutées (requirements.txt)
  - [x] opentelemetry-api
  - [x] opentelemetry-sdk
  - [x] opentelemetry-exporter-otlp-proto-grpc
  - [x] opentelemetry-instrumentation-requests

## 🔨 Intégration (À faire)

### 1. Agent principal (agents/travel_agent.py)

- [ ] Import de `get_telemetry`, `init_telemetry`
- [ ] Initialisation dans `__init__`
- [ ] Instrumentation de `chat()` avec span racine
- [ ] Instrumentation de `_detect_intent_semantic()` avec span
- [ ] Instrumentation des appels LLM avec `trace_llm_call()`
- [ ] Enregistrement des métriques de coût
- [ ] Ajout de `_estimate_cost()` pour calcul coût LLM

### 2. Tools (tools/travel_tools.py)

- [ ] Import de `get_telemetry`
- [ ] Instrumentation de `search_flights()` avec `trace_tool_call()`
- [ ] Instrumentation de `search_hotels()` avec `trace_tool_call()`
- [ ] Instrumentation de `get_airport_code()` avec `trace_tool_call()`
- [ ] Instrumentation des autres tools (restaurants, activities, etc.)
- [ ] Ajout d'attributs pertinents (params, résultats)

### 3. Streamlit (streamlit_app.py)

- [ ] Import de `init_telemetry`
- [ ] Initialisation au démarrage (une fois dans session_state)
- [ ] Configuration depuis variables d'environnement
- [ ] Gestion des erreurs avec télémétrie

### 4. Logger (utils/logger.py)

- [ ] Import de `trace` depuis opentelemetry
- [ ] Ajout de `_add_trace_context()` dans ContextLogger
- [ ] Modification de `info()`, `warning()`, `error()` pour inclure trace_id
- [ ] Test de la corrélation logs ↔ traces

### 5. Variables d'environnement

- [ ] Créer `.env` avec:
  ```
  OTLP_ENDPOINT=localhost:4317
  SERVICE_NAME=travel-agent
  SERVICE_VERSION=1.0.0
  ENVIRONMENT=development
  OTEL_CONSOLE_EXPORT=false
  ```

## 🧪 Tests (À faire)

### Tests locaux

- [ ] Démarrer la stack Grafana (`./start-observability.sh`)
- [ ] Vérifier que tous les services sont up
- [ ] Tester endpoint OTLP (nc -z localhost 4317)
- [ ] Lancer Streamlit avec instrumentation
- [ ] Faire quelques requêtes (small talk, planning, confirmation)
- [ ] Vérifier traces dans Tempo (http://localhost:3200)
- [ ] Vérifier métriques dans Prometheus (http://localhost:9090)
- [ ] Vérifier logs dans Loki via Grafana (http://localhost:3000)

### Tests de corrélation

- [ ] Vérifier que trace_id apparaît dans les logs JSON
- [ ] Dans Grafana Loki, cliquer sur trace_id → doit ouvrir trace dans Tempo
- [ ] Dans Grafana Tempo, voir les logs associés à une trace

### Tests de métriques

- [ ] Requêtes Prometheus:
  - [ ] `rate(agent_requests_total[5m])`
  - [ ] `histogram_quantile(0.95, rate(agent_request_duration_bucket[5m]))`
  - [ ] `sum(agent_llm_estimated_cost)`
  - [ ] `rate(agent_errors_total[5m])`

## 📊 Dashboards Grafana (À créer)

- [ ] Dashboard "Agent Performance"
  - [ ] Panel: Requests/sec par intent
  - [ ] Panel: Latence P50/P95/P99
  - [ ] Panel: Taux d'erreurs
  - [ ] Panel: Distribution des intents

- [ ] Dashboard "LLM Monitoring"
  - [ ] Panel: Tokens consommés par modèle
  - [ ] Panel: Coût estimé cumulé
  - [ ] Panel: Cache hit rate (Claude)
  - [ ] Panel: Latence LLM par modèle

- [ ] Dashboard "Tools Performance"
  - [ ] Panel: Tool calls par tool
  - [ ] Panel: Tool success rate
  - [ ] Panel: Tool latency distribution
  - [ ] Panel: Top slow tools

## 📚 Documentation (Complété)

- [x] OTLP_INTEGRATION.md - Guide complet d'intégration
- [x] OTLP_EXAMPLES.md - Exemples de code
- [x] README.md - Mise à jour avec section observabilité (à faire)

## 🚀 Déploiement

### Dev/Test
- [ ] Stack locale avec docker-compose
- [ ] Console export activé pour debug

### Production (futur)
- [ ] TLS activé sur OTLP endpoint
- [ ] Sampling configured (10% of traces)
- [ ] Retention policy adjusted
- [ ] Alerting configured in Grafana
- [ ] Rate limiting sur l'export

## 🎯 Priorités

**Phase 1 - Traces de base** (1-2h):
1. Intégrer `init_telemetry()` dans streamlit_app.py
2. Instrumenter `agent.chat()` avec span racine
3. Démarrer la stack et vérifier les traces dans Tempo

**Phase 2 - Tools et métriques** (1-2h):
4. Instrumenter les 3 tools principaux (flights, hotels, airport)
5. Vérifier les métriques dans Prometheus
6. Créer 1 dashboard simple dans Grafana

**Phase 3 - Corrélation logs** (30min):
7. Ajouter trace_id aux logs
8. Configurer derived fields dans Loki
9. Tester la navigation logs → traces

**Phase 4 - Métriques avancées** (1h):
10. Ajouter calcul de coût LLM
11. Instrumenter le prompt caching
12. Dashboard complet de monitoring

---

**Estimation totale**: 4-6 heures pour une implémentation complète

**Première étape recommandée**:
```bash
# Démarrer la stack
./start-observability.sh

# Vérifier que tout est up
docker-compose -f docker-compose.observability.yml ps

# Accéder à Grafana
open http://localhost:3000
```

**Prochaine action**: Intégrer `init_telemetry()` dans `streamlit_app.py`
