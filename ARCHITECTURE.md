# Architecture Overview

## System Design

This project implements a modular LangChain agent architecture with clear separation of concerns.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit App                             │
│                    (streamlit_app.py)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ creates & invokes
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Travel Agent                               │
│                   (agents/travel_agent.py)                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Model Factory                               │   │
│  │         (agents/model_factory.py)                        │   │
│  │                                                           │   │
│  │  ┌──────────────┐          ┌──────────────┐            │   │
│  │  │    Gemini    │          │    Claude    │            │   │
│  │  │  2.0 Flash   │          │  Sonnet 4    │            │   │
│  │  │ (Vertex AI)  │          │ (Anthropic)  │            │   │
│  │  └──────────────┘          └──────────────┘            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  System Prompt (2000+ tokens) + Tool Binding                    │
│  Iterative workflow: max 15 iterations                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ uses tools
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Travel Tools                                │
│                  (tools/travel_tools.py)                         │
│                                                                   │
│  12 LangChain @tool decorated functions                         │
│  ┌──────────────────┬──────────────────┬──────────────────┐    │
│  │ get_airport_code │ search_flights   │ search_hotels     │    │
│  ├──────────────────┼──────────────────┼──────────────────┤    │
│  │ search_rentals   │ find_cultural    │ recommend_rest    │    │
│  ├──────────────────┼──────────────────┼──────────────────┤    │
│  │ create_itinerary │ generate_map     │ calculate_cost    │    │
│  ├──────────────────┼──────────────────┼──────────────────┤    │
│  │ get_context      │ find_attractions │ recommend_package │    │
│  └──────────────────┴──────────────────┴──────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ delegates to
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Services Layer                            │
│                      (services/*.py)                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  FlightService          │  HotelService                │    │
│  │  (flight_service.py)    │  (hotel_service.py)          │    │
│  │  ├─ Amadeus API         │  ├─ Booking.com (RapidAPI)   │    │
│  │  └─ Mock fallback       │  └─ Mock fallback            │    │
│  ├─────────────────────────┼──────────────────────────────┤    │
│  │  RentalService          │  RestaurantService           │    │
│  │  (rental_service.py)    │  (restaurant_service.py)     │    │
│  │  ├─ SerpAPI             │  ├─ TravelAdvisor (RapidAPI) │    │
│  │  ├─ Airbnb (RapidAPI)   │  ├─ Foursquare API           │    │
│  │  └─ Mock fallback       │  └─ Mock fallback            │    │
│  ├─────────────────────────┼──────────────────────────────┤    │
│  │  CulturalService        │  LocationService             │    │
│  │  (cultural_service.py)  │  (location_service.py)       │    │
│  │  ├─ Overpass API        │  ├─ Geoapify API             │    │
│  │  └─ Mock fallback       │  └─ Nominatim (OSM)          │    │
│  ├─────────────────────────┼──────────────────────────────┤    │
│  │  WikipediaService       │  AirportService              │    │
│  │  (wikipedia_service.py) │  (airport_service.py)        │    │
│  │  ├─ Wikipedia API       │  ├─ Amadeus API              │    │
│  │  └─ 5s timeout + retry  │  └─ Hardcoded fallback dict  │    │
│  └─────────────────────────┴──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ logs to
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Layer                           │
│                       (utils/*.py)                               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ContextLogger (logger.py)                             │    │
│  │  ├─ Structured JSON logs → logs/app.json.log          │    │
│  │  ├─ Context propagation (request tracking)             │    │
│  │  └─ Log levels: INFO, WARNING, ERROR                   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Prometheus Metrics (logger.py)                        │    │
│  │  ├─ llm_latency_seconds (Histogram)                    │    │
│  │  ├─ agent_iterations (Gauge)                           │    │
│  │  └─ app_log_messages_total (Counter)                   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Metrics Server (metrics_server.py)                    │    │
│  │  └─ Flask endpoint: http://localhost:8000/metrics      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. User Request
```
User → Streamlit UI → "I want to go to Tokyo in April"
```

### 2. Agent Processing
```
TravelAgent.plan_trip()
├─ Create message chain: [SystemMessage, HumanMessage]
├─ Start iteration loop (max 15)
│  ├─ Invoke LLM with tools bound
│  │  └─ Log: llm_latency metric
│  ├─ LLM decides which tools to call
│  └─ Execute tools sequentially
│     ├─ get_airport_code("Tokyo") → "NRT"
│     ├─ search_flights(origin="CDG", dest="NRT") → Flight list
│     ├─ search_hotels(city="Tokyo") → Hotel list
│     ├─ search_vacation_rentals(city="Tokyo") → Rental list
│     ├─ find_cultural_activities(city="Tokyo") → Activities
│     ├─ recommend_restaurants(city="Tokyo") → Restaurants
│     ├─ create_visit_itinerary(city="Tokyo") → 7-day plan
│     ├─ generate_travel_map(city="Tokyo") → HTML map
│     ├─ calculate_total_cost() → Budget breakdown
│     └─ recommend_best_package() → Best option
├─ Add tool results to message chain
├─ LLM generates final response
└─ Return formatted recommendation
```

### 3. Logging Flow
```
Every operation:
├─ ContextLogger.info/warning/error()
│  ├─ Writes to logs/app.json.log
│  └─ Updates Prometheus counters
└─ Metrics exposed at :8000/metrics
```

## Design Patterns

### 1. Factory Pattern
**Location:** `agents/model_factory.py`

```python
ModelFactory.create_llm(provider=ModelProvider.GEMINI)
→ Returns ChatVertexAI or ChatAnthropic
```

**Benefits:**
- Easy to switch between LLMs
- Centralized configuration
- Consistent interface

### 2. Singleton Pattern
**Location:** `services/*.py`

```python
_service_instance: Optional[ServiceClass] = None

def get_service() -> ServiceClass:
    global _service_instance
    if _service_instance is None:
        _service_instance = ServiceClass()
    return _service_instance
```

**Benefits:**
- Single API client instance
- Shared caching
- Resource efficiency

### 3. Decorator Pattern
**Location:** `tools/travel_tools.py`

```python
@tool
def search_flights(origin: str, destination: str) -> str:
    """Search for available flights"""
    service = get_flight_service()
    return service.search(origin, destination)
```

**Benefits:**
- LangChain automatic schema generation
- Type hints for validation
- Clean separation of concerns

### 4. Strategy Pattern (Fallback)
**Location:** All services

```python
def search():
    try:
        # Try real API
        return api_client.search()
    except Exception:
        # Fallback to mock data
        return mock_data.get()
```

**Benefits:**
- Graceful degradation
- Always returns data
- Testable without APIs

## Data Flow

### Input Processing
```
Natural Language → LLM → Structured Parameters → API Calls
"Tokyo in April" → {city: "Tokyo", dates: "2026-04", travelers: 2}
```

### Tool Execution
```
Tool Request → Service Layer → External API → Response → Tool Result
search_flights → FlightService → Amadeus API → JSON → Formatted string
```

### Response Generation
```
Tool Results → LLM Context → Final Response → User
[flights, hotels, ...] → Markdown formatted → Streamlit display
```

## Performance Characteristics

### Latency Breakdown
```
Total request time: 30-90s
├─ LLM calls: 1-3s per iteration (3-10 iterations)
├─ API calls: 1-20s per tool (parallel execution possible)
├─ Tool execution: 0.001-0.1s overhead
└─ Logging: <0.001s per log entry
```

### Optimization Strategies
1. **Parallel tool execution** - Call independent tools simultaneously
2. **Caching** - Store API results (future: Redis)
3. **Prompt optimization** - Reduce token count
4. **Mock fallback** - Skip slow APIs when acceptable

## Error Handling

### Levels
```
1. API Level (services/)
   └─ Try API → Catch exception → Return mock data

2. Tool Level (tools/)
   └─ Try service → Catch exception → Return error string

3. Agent Level (agents/)
   └─ Try tool → Log error → Continue iteration

4. App Level (streamlit_app.py)
   └─ Try agent → Display error → Allow retry
```

### Logging Strategy
```
INFO  - Successful operations
WARN  - Fallback to mock data
ERROR - Exceptions with stack trace
```

## Security Considerations

### Secrets Management
```
Environment Variables (.env)
├─ ANTHROPIC_API_KEY
├─ GOOGLE_CLOUD_PROJECT
├─ AMADEUS_API_KEY
├─ RAPIDAPI_KEY
└─ etc.

Never committed to git (.gitignore)
```

### API Rate Limiting
```
Service Level Limits:
├─ Amadeus: 2000 req/month (free tier)
├─ RapidAPI: Varies by endpoint
└─ Wikipedia: No official limit (be respectful)

Mitigation: Mock fallback + caching
```

## Extensibility

### Adding a New Tool
```python
# 1. Create service (services/new_service.py)
class NewService:
    def search(self, query: str) -> List[Result]:
        # Implementation

# 2. Add tool (tools/travel_tools.py)
@tool
def new_tool(query: str) -> str:
    """Description for LLM"""
    service = get_new_service()
    results = service.search(query)
    return format_results(results)

# 3. Register tool (streamlit_app.py)
tools = get_all_tools() + [new_tool]
```

### Adding a New LLM
```python
# 1. Update ModelFactory (agents/model_factory.py)
class ModelProvider(Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    NEW_MODEL = "new_model"  # Add this

# 2. Add configuration
MODELS = {
    ModelProvider.NEW_MODEL: {
        "name": "New Model",
        "model": "new-model-id",
        "api_key_env": "NEW_MODEL_API_KEY",
        "class": ChatNewModel
    }
}
```

## Testing Strategy

### Current State
- No unit tests (lab project)
- Manual testing via Streamlit
- Log analysis for debugging

### Production Recommendations
```
tests/
├─ unit/
│  ├─ test_services.py     # Mock API responses
│  ├─ test_tools.py        # Tool input/output
│  └─ test_agent.py        # Agent workflow
├─ integration/
│  ├─ test_api_clients.py  # Real API calls (slow)
│  └─ test_end_to_end.py   # Full workflow
└─ fixtures/
   └─ mock_responses.json   # Sample API data
```

## Future Improvements

### Phase 1: Stability
- [ ] Unit tests (80% coverage)
- [ ] Fix Prometheus metrics duplication
- [ ] Add Osaka to airport codes
- [ ] Increase Wikipedia timeout

### Phase 2: Performance
- [ ] Redis caching layer
- [ ] Parallel tool execution
- [ ] Prompt size optimization
- [ ] Connection pooling

### Phase 3: Observability
- [ ] OpenTelemetry instrumentation
- [ ] Grafana dashboards
- [ ] Distributed tracing
- [ ] Alert rules

### Phase 4: Production
- [ ] CI/CD pipeline
- [ ] Rate limiting middleware
- [ ] API key rotation
- [ ] Health check endpoints
