
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
├── agents/              # Main LangChain agent
│   ├── travel_agent.py  # Unified multi-model agent
│   └── model_factory.py # Factory for Gemini/Claude
├── services/            # External API services
│   ├── flight_service.py
│   ├── hotel_service.py
│   ├── rental_service.py
│   └── restaurant_service.py
├── tools/               # LangChain tools
│   └── travel_tools.py  # 12 tools with @tool decorator
├── utils/               # Logging & Metrics
│   ├── logger.py
│   └── metrics_server.py
└── streamlit_app.py     # Web interface
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed component diagrams and design patterns.

## Installation

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI enabled
- API keys: Amadeus, RapidAPI, Anthropic

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp .env.example .env
# Edit .env with your API keys

# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## Usage

### Web Interface (Recommended)
```bash
streamlit run streamlit_app.py
```

### CLI Mode
```python
from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider
from tools.travel_tools import get_all_tools

agent = TravelAgent(
    tools=get_all_tools(),
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

## Monitoring

### Structured Logs
```bash
tail -f logs/app.json.log
```

### Prometheus Metrics
Endpoint: `http://localhost:8000/metrics`

Available metrics:
- `llm_latency_seconds` - LLM response time
- `agent_iterations` - Iterations per request
- `app_log_messages_total` - Log counter by level

## Test Results

| Destination | Status | Duration | Iterations | Notes |
|-------------|--------|----------|------------|-------|
| Cuba | SUCCESS | 39s | 5 | All APIs functional |
| Tokyo | SUCCESS | 38s | 2 | Aggressive optimization |
| New York | SUCCESS | 86s | 3 | Wikipedia timeout + retry |
| Perpignan | SUCCESS | 60s | 10 | Fallback to mock data |
| Osaka | FAILURE | 7s | 5 | Missing airport code |

## Known Issues

1. **Prometheus metrics duplication** - Streamlit crashes on hot reload
   - Fix: Implement singleton pattern in `utils/logger.py`

2. **Missing Osaka airport code** - Agent loops for 5 iterations
   - Fix: Add `"Osaka": "KIX"` to `services/airport_service.py`

3. **Wikipedia timeout** - 5s timeout too short for international requests
   - Fix: Increase to 10s or implement exponential backoff

## Key Learnings

### What Works Well
- LangChain tool binding provides clean, intuitive API
- Gemini 2.0 Flash delivers excellent performance (fast + cost-effective)
- 3-10 iterations sufficient for complete workflow
- Fallback mock data enables graceful degradation

### Challenges
- Token consumption: Long prompts (2000+ tokens) increase costs
- API rate limits: Amadeus free tier limited to 2000 req/month
- Latency: 30-90s for complete search depending on APIs
- Prometheus metrics require careful handling with Streamlit hot reload

## Next Steps

1. **OpenTelemetry + Grafana Integration** (Next Lab)
   - Distributed tracing
   - Real-time dashboards
   - Error alerting

2. **Performance Optimizations**
   - Redis caching for API results
   - Parallel tool execution
   - Prompt size reduction

3. **Production Readiness**
   - Unit tests + CI/CD
   - Rate limiting
   - Enhanced error handling

## License

MIT - Educational experimental project

## Contributing

Personal lab project - contributions not expected