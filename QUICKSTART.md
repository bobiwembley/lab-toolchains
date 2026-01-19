# 🚀 Quick Start Guide

## Quick Installation

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for observability)
- API keys: Google Cloud (Vertex AI), Anthropic, Amadeus, RapidAPI

### 2. Application Setup

```bash
# Install dependencies
pip install -r app/requirements.txt

# Configure secrets
cp .env.example .env
# Edit .env with your API keys

# Google Cloud authentication (for Gemini)
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Launch Application

#### Option A: Web Interface (Streamlit)
```bash
streamlit run app/streamlit_app.py
```
Open http://localhost:8501

#### Option B: CLI Chatbot
```bash
python app/main.py
```

### 4. (Optional) Observability Stack

```bash
# Start Grafana + Tempo + Loki + Prometheus
cd observability
./start-observability.sh

# Access
# - Grafana:    http://localhost:3000
# - Prometheus: http://localhost:9090
# - Tempo:      http://localhost:3200

# Diagnostic
./check_otlp.sh

# Stop
docker-compose down
```

## Useful Commands

### Logs
```bash
# View structured logs
tail -f logs/app.json.log | jq

# Filter by intent
tail -f logs/app.json.log | jq -r 'select(.intent == "planning") | .message'
```

### Tests
```bash
# Unit tests
cd tests
python -m pytest test_travel_agent_chat.py -v

# Verify optimizations
python -c "from app.agents.travel_agent import TravelAgent; print('✅ Imports OK')"
```

### Docker (Observability)
```bash
cd observability

# Status
docker-compose ps

# Logs
docker-compose logs -f otel-collector
docker-compose logs -f tempo

# Restart
docker-compose restart tempo
```

## Usage Examples

### Python API
```python
import sys
sys.path.insert(0, 'app')

from agents.travel_agent import TravelAgent
from agents.model_factory import ModelProvider
from tools.travel_tools import create_all_tools

# Create agent
agent = TravelAgent(
    tools=create_all_tools(),
    model_provider=ModelProvider.GEMINI,  # or CLAUDE
    fast_mode=False  # True for fast mode (5 tools)
)

# Multi-turn conversation
agent.chat("I want to travel")
agent.chat("To Japan")
result = agent.chat("To Tokyo in April for 1 week")
print(result)

# Reset
agent.reset_conversation()
```

### CLI Chatbot
```bash
$ python app/main.py

🌍 Travel Agent Chatbot
💬 You: I'm looking for a trip
🤖 Assistant: With pleasure! Where would you like to travel?
💬 You: To Japan
🤖 Assistant: Which destination specifically in Japan?
💬 You: Tokyo in April
🤖 Assistant: [searching flights, hotels, activities...]

Commands: reset, history, help, exit
```

## Troubleshooting

### Error: "No module named 'agents'"
```bash
# Solution: Add app/ to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/app"
python app/main.py
```

### Streamlit won't start
```bash
# Kill old processes
pkill -f streamlit

# Restart
streamlit run app/streamlit_app.py --server.port 8501
```

### Docker: Port 4317 already in use
```bash
# Find the process
lsof -i :4317

# Stop containers
cd observability
docker-compose down
```

### Traces not showing in Tempo
- ✅ HTTP auto-instrumentation working (see Phase 1 in OTLP_STATUS.md)
- ⏳ Custom spans require refactoring (Phase 2)
- Check: `./check_otlp.sh` in observability/

## Documentation

- [README.md](README.md) - Complete overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [app/docs/IMPROVEMENTS_SUMMARY.md](app/docs/IMPROVEMENTS_SUMMARY.md) - Optimization history
- [app/docs/OTLP_STATUS.md](app/docs/OTLP_STATUS.md) - Observability status

## Support

Experimental lab project - no official support.
See GitHub issues for known problems.
