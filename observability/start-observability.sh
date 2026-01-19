#!/bin/bash

# Script de démarrage de la stack d'observabilité Grafana

set -e

echo "🚀 Démarrage de la stack d'observabilité Grafana..."

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Installation requise."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Installation requise."
    exit 1
fi

# Créer les volumes si nécessaire
echo "📦 Création des volumes Docker..."
docker volume create --name grafana-storage 2>/dev/null || true
docker volume create --name tempo-data 2>/dev/null || true
docker volume create --name loki-data 2>/dev/null || true
docker volume create --name prometheus-data 2>/dev/null || true

# Démarrer les services
echo "🐳 Démarrage des conteneurs..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services (30s)..."
sleep 30

# Vérifier le statut
echo ""
echo "✅ Services démarrés:"
docker-compose ps

# Afficher les URLs
echo ""
echo "🌐 URLs d'accès:"
echo "  - Grafana:     http://localhost:3000"
echo "  - Tempo:       http://localhost:3200"
echo "  - Loki:        http://localhost:3100"
echo "  - Prometheus:  http://localhost:9090"
echo "  - OTLP gRPC:   localhost:4317"
echo ""

# Tester la connectivité OTLP
echo "🔍 Test de l'endpoint OTLP..."
if nc -z localhost 4317 2>/dev/null; then
    echo "✅ OTLP Collector est accessible sur localhost:4317"
else
    echo "⚠️  OTLP Collector n'est pas encore accessible. Attendre quelques secondes."
fi

echo ""
echo "📊 Pour voir les logs du collector:"
echo "  docker-compose logs -f otel-collector"
echo ""
echo "🛑 Pour arrêter la stack:"
echo "  docker-compose down"
echo ""
echo "✨ Stack d'observabilité prête!"
