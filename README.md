# LangChain Multi-Model Travel Agent Lab

Experimental lab testing LangChain with Gemini 2.0 Flash (Google Vertex AI) and Claude Sonnet (Anthropic) for building a multi-tool conversational agent.

## Overview

This project explores LangChain's agent framework to create a travel planning assistant with:
- Multi-model LLM support (Gemini 2.0 Flash & Claude Sonnet 4)
- Tool binding with 12 integrated tools (flights, hotels, restaurants, etc.)
- Iterative agent workflow with multi-step reasoning
- Structured JSON logging with Prometheus metrics
- Streamlit web interface

## Architecture

```
lab-toolchains/
├── agents/                           # 🤖 Logique de l'agent
│   └── travel_agent.py               # TravelAgent class
├── tools/                            # 🔧 LangChain Tools
│   └── travel_tools.py               # @tool decorators
├── services/                         # 💼 Services métier
│   └── flight_service.py             # SerpAPI integration
├── models/                           # 🧠 Wrappers LLM
│   └── claude_client.py              # Claude wrapper
├── cli/                              # 🖥️ Interface CLI
│   └── interface.py                  # Interactive mode
└── professional_travel_agent.py      # 🎯 Entry point (50 lignes)
```

**Architecture modulaire** : Chaque module ≈ 50-120 lignes, hautement réutilisable.  
📖 Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour les détails.

## 🛠️ Fonctionnalités

### ✅ Actuelles

- ✈️ **Recherche de vols** avec prix réels via SerpAPI
- 🏨 **Recherche d'hôtels** (données mock)
- 💰 **Calcul du coût total** pour plusieurs voyageurs
- 🤖 **Dialogue intelligent** avec Claude Sonnet 4
- 🔄 **Mode interactif** avec conversation continue
- 🛡️ **Fallback automatique** sur données mock si API indisponible

### 🚧 Roadmap

- [ ] Intégration API hôtels réelle
- [ ] Support multi-destinations
- [ ] Export des recommandations (PDF, JSON)
- [ ] Interface web (Streamlit)

## 📊 Exemple de Sortie

```
✈️ Vols CDG → HAV (2026-03-15):

1. Iberia - $2211.0 USD
   1 escale(s) • Durée: 15h 40m
   Départ: 07:00 → Arrivée: 17:40

💰 Meilleur prix: $2211.0 avec Iberia

🏨 Hôtels à Havana (7 nuits):
1. Hotel Nacional - $840 total

💵 COÛT TOTAL: $4737 pour 2 personnes
```

## 🐛 Troubleshooting

**Erreur "ANTHROPIC_API_KEY required"**  
→ Vérifier `.env` contient `ANTHROPIC_API_KEY=...`

**Vols mock au lieu de prix réels**  
→ Ajouter `SERPAPI_KEY` dans `.env`

## 📚 Documentation

- [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md) : Guide détaillé

---

**Développé avec ❤️ et les best practices**
