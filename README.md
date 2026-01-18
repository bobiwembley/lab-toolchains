# 🌴 Agent de Voyage Intelligent - Claude + SerpAPI

Agent de voyage professionnel utilisant **Claude Sonnet 4** et **SerpAPI** pour trouver les meilleurs prix de vols en temps réel.

## 🚀 Installation

```bash
# Cloner le projet
git clone <votre-repo>
cd lab-toolchains

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt
```

## 🔑 Configuration

Créer un fichier `.env` à la racine :

```bash
# OBLIGATOIRE - Claude API
ANTHROPIC_API_KEY=sk-ant-api03-...

# OPTIONNEL - SerpAPI pour prix réels (sinon mock data)
SERPAPI_KEY=votre_clé_serpapi
```

### Obtenir les clés API

- **Claude API** : https://console.anthropic.com/
- **SerpAPI** : https://serpapi.com/ (100 recherches gratuites/mois)

## 📖 Utilisation

### Mode Interactif (Recommandé)

```bash
python professional_travel_agent.py
```

**Commandes disponibles :**
- Tapez votre demande de voyage en langage naturel
- `aide` - Afficher l'aide
- `quitter` - Sortir du programme

### Exemples de demandes

```
Je veux aller à Cuba depuis Paris en mars 2026 pour 2 personnes

Trouve-moi un vol Paris-New York pour le 15 avril avec hôtel 5 nuits

Voyage à Tokyo depuis CDG, départ 1er juin, retour 10 juin, 1 personne
```

## 🏗️ Architecture Modulaire

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
