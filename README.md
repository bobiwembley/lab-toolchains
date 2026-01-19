
# LangChain Multi-Model Travel Agent Lab

Experimental lab testing LangChain with Gemini 2.0 Flash (Google Vertex AI) and Claude Sonnet (Anthropic) for building a multi-tool conversational agent.

> **📁 Project reorganized** - Code in `app/`, infrastructure in `observability/`  
> **🚀 Quick start:** [QUICKSTART.md](QUICKSTART.md) | **📚 Documentation index:** [INDEX.md](INDEX.md)

## 🆕 Version 2.0 - Optimized with Semantic Intent Detection

**Latest improvements:**
- ✅ **Semantic intent detection** with LLM (94.1% accuracy)
- ✅ **Prompt caching** for Claude & Gemini (-90% cost, -9% latency)
- ✅ **Conditional prompts** (light/fast/full) based on context
- ✅ **Confirmation handling** ("fais le", "go") with automatic tool execution
- ✅ **0% empty responses** (max_iterations fixed: 5-8 vs 2-3)

See [docs/IMPROVEMENTS_SUMMARY.md](docs/IMPROVEMENTS_SUMMARY.md) for full details.

## Overview

This project explores LangChain's agent framework to create a travel planning assistant with:
- **🆕 Semantic intent detection** (small_talk, confirmation, planning)
- **🆕 Intelligent prompt selection** with caching
- Multi-model LLM support (Gemini 2.0 Flash & Claude Sonnet 4)
- Tool binding with 12 integrated tools (flights, hotels, restaurants, etc.)
- Iterative agent workflow with multi-step reasoning
- Structured JSON logging with Prometheus metrics
- Streamlit web interface

## Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Small talk latency | 3-5s | 1-2s | -60% |
| Planning latency | 8-12s | 6-8s | -30% |
| Empty responses | 30-40% | 0% | -100% |
| Cost per request | $0.069 | $0.007-0.069 | -90% (cached) |
| Intent accuracy | 82% | 94.1% | +12% |

## Architecture

```
lab-toolchains/
├── app/                     # Application principale
│   ├── agents/              # LangChain agent
│   │   ├── travel_agent.py  # Unified multi-model agent
│   │   └── model_factory.py # Factory for Gemini/Claude
│   ├── services/            # External API services
│   │   ├── flight_service.py
│   │   ├── hotel_service.py
│   │   ├── rental_service.py
│   │   └── restaurant_service.py
│   ├── tools/               # LangChain tools
│   │   └── travel_tools.py  # 12 tools with @tool decorator
│   ├── utils/               # Utilities
│   │   ├── logger.py        # Structured logging
│   │   ├── metrics_server.py # Prometheus metrics
│   │   └── telemetry.py     # OpenTelemetry (OTLP)
│   ├── docs/                # Documentation
│   │   ├── IMPROVEMENTS_SUMMARY.md  # Improvements log
│   │   ├── INTENT_DETECTION.md      # Intent detection
│   │   ├── OTLP_INTEGRATION.md      # OpenTelemetry guide
│   │   ├── OTLP_EXAMPLES.md         # Code examples
│   │   └── OTLP_STATUS.md           # Current status
│   ├── streamlit_app.py     # Web UI
│   ├── main.py              # CLI chatbot
│   └── requirements.txt     # Python dependencies
├── observability/           # Infrastructure d'observabilité
│   ├── docker-compose.yml   # Grafana stack (Tempo/Loki/Prometheus)
│   ├── start-observability.sh # Quick start script
│   ├── check_otlp.sh        # Diagnostic tool
│   ├── grafana/             # Grafana datasources config
│   ├── tempo/               # Tempo config (traces)
│   ├── prometheus/          # Prometheus config (metrics)
│   └── otel-collector/      # OTLP Collector config
├── examples/                # Exemples d'utilisation
├── tests/                   # Tests unitaires
├── logs/                    # Logs de l'application
├── ARCHITECTURE.md          # System design
└── README.md
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed component diagrams and design patterns.

## Installation

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (for observability)
- Google Cloud Project with Vertex AI enabled
- API keys: Amadeus, RapidAPI, Anthropic

### Quick Setup

```bash
# Install dependencies
pip install -r app/requirements.txt

# Configure secrets
cp .env.example .env
# Edit .env with your API keys

# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

📖 **See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions**

## Usage

### 🆕 Interactive Chatbot (New!)
```bash
# Launch the interactive chatbot interface
python app/main.py
```

Features:
- Multi-turn conversations with memory
- Progressive query refinement
- Commands: `reset`, `history`, `help`, `exit`

### Web Interface
```bash
streamlit run app/streamlit_app.py
```

### Programmatic Usage

#### Option 1: Chatbot Mode (with memory)
```python
# Ajouter app/ au PYTHONPATH
import sys
sys.path.insert(0, 'app')

from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider
from tools.travel_tools import create_all_tools

agent = TravelAgent(
    tools=create_all_tools(),
    model_provider=ModelProvider.CLAUDE,
    temperature=0.7
)

# Multi-turn conversation
agent.chat("I want to travel")
agent.chat("To Japan")
result = agent.chat("To Tokyo in April")  # Context preserved!
print(result)

# Reset for new conversation
agent.reset_conversation()
```

#### Option 2: One-Shot Mode (backward compatible)
```python
agent = TravelAgent(
    tools=create_all_tools(),
    model_provider=ModelProvider.GEMINI,
    temperature=0.7
)

result = agent.plan_trip("I want to go to Tokyo in April")
print(result)
```

## Available Tools

| Tool | Description | API |
|------|-------------|-----|
| get_airport_code | IATA airport code lookup | Amadeus + fallback |
| get_destination_context | Wikipedia context | Wikipedia API |
| search_flights | Flight search | Amadeus Flight Offers |
| search_hotels | Hotel search | Booking.com (RapidAPI) |
| search_vacation_rentals | Vacation rentals | Airbnb (RapidAPI) |
| find_cultural_activities | Museums, monuments | Geoapify |
| find_nearby_attractions | Points of interest | Geoapify |
| recommend_restaurants | Restaurant recommendations | TravelAdvisor |
| create_visit_itinerary | 7-day itinerary generator | LLM-generated |
| generate_travel_map | Interactive HTML map | Folium |
| calculate_total_cost | Budget calculation | Internal |
| recommend_best_package | Package recommendation | Multi-criteria |

## Monitoring & Observability

### 🆕 OpenTelemetry (OTLP) - Production-Grade Observability

Full instrumentation with export to **Grafana Stack** (Tempo + Loki + Prometheus):

```bash
# Start the Grafana stack
cd observability
./start-observability.sh

# Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
```

**Available observability:**
- **Distributed tracing** (Tempo): HTTP request traces with auto-instrumentation
- **Centralized logging** (Loki): Structured JSON logs ready for correlation
- **Metrics** (Prometheus): LLM tokens, costs, latency, tool performance
- **Dashboards** (Grafana): Pre-configured datasources for exploration

**Current status: ⚠️ Phase 1 partielle**
- ✅ HTTP auto-instrumentation working (RequestsInstrumentor)
- ⏳ Custom spans pending (architectural refactoring required)

See [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) for detailed status and Phase 2 roadmap.
See [app/docs/OTLP_INTEGRATION.md](app/docs/OTLP_INTEGRATION.md) for complete setup guide.

**Key metrics:**
- `agent.requests.total` - Requests by intent (small_talk/confirmation/planning)
- `agent.request.duration` - Latency histograms (P50/P95/P99)
- `agent.llm.tokens` - Token consumption by model (cached vs non-cached)
- `agent.llm.estimated_cost` - Real-time cost tracking
- `agent.tool.calls` - Tool execution counts and success rates
- `agent.errors.total` - Error tracking by type

### Structured Logs
```bash
tail -f logs/app.json.log | jq
```

Example log with trace correlation:
```json
{
  "timestamp": "2026-01-19T10:30:00Z",
  "level": "INFO",
  "message": "Chat message received",
  "intent": "planning",
  "trace_id": "a1b2c3d4e5f6...",
  "span_id": "1234567890ab"
}
```## Documentation

- **[Improvements Summary](app/docs/IMPROVEMENTS_SUMMARY.md)** - Complete optimization history
- **[Intent Detection](app/docs/INTENT_DETECTION.md)** - Technical deep dive on semantic detection
- **[OTLP Integration](app/docs/OTLP_INTEGRATION.md)** - OpenTelemetry setup guide (Grafana stack)
- **[OTLP Status](app/docs/OTLP_STATUS.md)** - Current implementation status and Phase 2 roadmap
- **[OTLP Examples](app/docs/OTLP_EXAMPLES.md)** - Instrumentation code examples
- **[Architecture](ARCHITECTURE.md)** - System design and components

## Key Learnings

### What Works Well
- **🆕 Conversation memory enables natural progressive refinement**
- **🆕 Context preservation across multiple turns improves UX**
- LangChain tool binding provides clean, intuitive API
- Gemini 2.0 Flash delivers excellent performance (fast + cost-effective)
- 3-10 iterations sufficient for complete workflow
- Fallback mock data enables graceful degradation

### Challenges
- Token consumption: Long prompts (2000+ tokens) increase costs
- **🆕 Context window management needed for long conversations**
## Test Results

| Destination | Status | Duration | Iterations | Notes |
|-------------|--------|----------|------------|-------|
| Cuba | SUCCESS | 39s | 5 | All APIs functional |
| Tokyo | SUCCESS | 38s | 2 | Aggressive optimization |
| New York | SUCCESS | 86s | 3 | Wikipedia timeout + retry |
| Perpignan | SUCCESS | 60s | 10 | Fallback to mock data |
| Osaka | FAILURE | 7s | 5 | Missing airport code |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Project architecture and design
- [docs/IMPROVEMENTS_SUMMARY.md](docs/IMPROVEMENTS_SUMMARY.md) - Complete improvements summary
- [docs/INTENT_DETECTION.md](docs/INTENT_DETECTION.md) - Intent detection implementation details

## Known Issues

1. **Amadeus API errors (400)** - Invalid date format or exceeded quota
   - Fix: Validate dates, fallback to mock data active

2. **Booking.com destination IDs** - Some cities not found
   - Fix: Enhanced location search, mock data fallback

3. **Fast mode tools** - Cultural activities/restaurants not available
   - Status: Documented in SYSTEM_PROMPT_FAST

## Key Learnings

### What Works Well
- ✅ **Semantic intent detection** with LLM provides excellent accuracy (94.1%)
- ✅ **Prompt caching** drastically reduces costs and latency
- ✅ **Conditional prompts** optimize for each use case
- ✅ **Confirmation workflow** extracts context and executes automatically
- ✅ LangChain tool binding provides clean, intuitive API
- ✅ Gemini 2.0 Flash delivers excellent performance (fast + cost-effective)
- ✅ Fallback mock data enables graceful degradation

### Challenges Resolved
- ✅ Empty responses → Fixed with max_iterations 5-8
- ✅ Unknown tool errors → Fixed with conditional prompts
- ✅ High latency on greetings → Fixed with intent detection
- ✅ Confirmation not triggering tools → Fixed with semantic detection

## Next Steps

1. **API Integration Improvements**
   - Fix Amadeus date formatting
   - Implement Booking.com destination ID cache
   - Add retry logic with exponential backoff

2. **Performance Monitoring**
   - OpenTelemetry + Grafana integration
   - Real-time dashboards for latency/costs
   - Intent detection accuracy tracking

3. **Production Features**
   - Unit tests + CI/CD
   - Rate limiting per user
   - Multi-language support

## License

MIT - Educational experimental project

## Contributing

Personal lab project - contributions not expected