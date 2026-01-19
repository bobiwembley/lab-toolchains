#!/bin/bash
# Script de diagnostic OpenTelemetry
# Usage: ./check_otlp.sh

echo "🔍 Diagnostic OpenTelemetry - Travel Agent"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier les services Docker
echo "📦 Services Docker"
echo "------------------"
if docker compose -f docker-compose.observability.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services actifs:${NC}"
    docker compose -f docker-compose.observability.yml ps | grep "Up" | awk '{print "  - " $1 " (" $5 ")"}'
else
    echo -e "${RED}❌ Aucun service actif${NC}"
    echo "   Lancer: docker compose -f docker-compose.observability.yml up -d"
fi
echo ""

# 2. Vérifier les endpoints
echo "🌐 Endpoints"
echo "-------------"
endpoints=(
    "Grafana:http://localhost:3000"
    "Prometheus:http://localhost:9090"
    "Tempo:http://localhost:3200/ready"
    "Loki:http://localhost:3100/ready"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r name url <<< "$endpoint"
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo -e "${GREEN}✅ $name${NC} - $url"
    else
        echo -e "${RED}❌ $name${NC} - $url (not responding)"
    fi
done
echo ""

# 3. Vérifier les traces dans Tempo
echo "🔗 Traces dans Tempo"
echo "--------------------"
trace_count=$(curl -s 'http://localhost:3200/api/search' | jq -r '.traces | length' 2>/dev/null)
if [ "$trace_count" -gt 0 ]; then
    echo -e "${GREEN}✅ $trace_count traces trouvées${NC}"
    echo "   Dernières traces:"
    curl -s 'http://localhost:3200/api/search' | jq -r '.traces[:3] | .[] | "  - \(.traceID[0:16])... (\(.durationMs)ms) - \(.rootServiceName)"' 2>/dev/null
else
    echo -e "${YELLOW}⚠️  Aucune trace trouvée${NC}"
    echo "   Les traces apparaissent après utilisation de l'app"
fi
echo ""

# 4. Vérifier les logs récents
echo "📝 Logs récents (app.json.log)"
echo "-------------------------------"
if [ -f "logs/app.json.log" ]; then
    last_otel=$(tail -100 logs/app.json.log | jq -r 'select(.message | contains("OpenTelemetry")) | .timestamp + " - " + .message' 2>/dev/null | tail -1)
    if [ -n "$last_otel" ]; then
        echo -e "${GREEN}✅ OpenTelemetry actif:${NC}"
        echo "   $last_otel"
    else
        echo -e "${YELLOW}⚠️  Pas d'init OpenTelemetry récent${NC}"
    fi
    
    # Vérifier trace_id
    trace_count=$(tail -200 logs/app.json.log | jq -r 'select(.trace_id) | .trace_id' 2>/dev/null | wc -l)
    if [ "$trace_count" -gt 0 ]; then
        echo -e "${GREEN}✅ $trace_count logs avec trace_id${NC}"
    else
        echo -e "${YELLOW}⚠️  Aucun log avec trace_id (spans customisés non actifs)${NC}"
    fi
else
    echo -e "${RED}❌ Fichier logs/app.json.log introuvable${NC}"
fi
echo ""

# 5. Vérifier OTLP Collector
echo "📡 OTLP Collector"
echo "-----------------"
collector_logs=$(docker logs otel-collector --tail 10 2>&1)
if echo "$collector_logs" | grep -q "Everything is ready"; then
    echo -e "${GREEN}✅ Collector opérationnel${NC}"
    
    # Compter les spans reçus
    span_count=$(docker logs otel-collector --since 5m 2>&1 | grep -c "ResourceSpans" || echo "0")
    if [ "$span_count" -gt 0 ]; then
        echo -e "${GREEN}✅ $span_count ResourceSpans reçus (5 dernières minutes)${NC}"
    else
        echo -e "${YELLOW}⚠️  Aucun span reçu récemment${NC}"
    fi
else
    echo -e "${RED}❌ Collector pas prêt${NC}"
    echo "   Logs: docker logs otel-collector --tail 20"
fi
echo ""

# 6. Résumé et recommandations
echo "📊 Résumé"
echo "---------"
if [ "$trace_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Infrastructure OpenTelemetry opérationnelle${NC}"
    echo ""
    echo "🎯 Accès rapides:"
    echo "   - Grafana: http://localhost:3000"
    echo "   - Tempo traces: http://localhost:3000/explore (Query: {service.name=\"travel-agent\"})"
    echo ""
    echo "⚠️  Note: Seules les traces HTTP auto-instrumentées sont visibles"
    echo "   Pour des spans customisés (agent.intent, etc.), voir docs/OTLP_STATUS.md Phase 2"
else
    echo -e "${YELLOW}⚠️  Infrastructure prête mais pas de traces${NC}"
    echo ""
    echo "📝 Actions:"
    echo "   1. Lancer l'app: streamlit run streamlit_app.py"
    echo "   2. Envoyer un message dans le chat"
    echo "   3. Relancer: ./check_otlp.sh"
fi
echo ""
