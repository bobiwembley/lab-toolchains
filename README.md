
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