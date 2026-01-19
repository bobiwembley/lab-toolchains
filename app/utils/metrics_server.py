"""
Endpoint Prometheus pour exposer les métriques
À monter dans Streamlit ou Flask pour scraping
"""

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flask import Flask, Response
import os

app = Flask(__name__)


@app.route('/metrics')
def metrics():
    """
    Endpoint pour scraping Prometheus
    
    Returns:
        Métriques au format Prometheus
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'travel-agent'}, 200


if __name__ == '__main__':
    # Port configurable via env
    port = int(os.getenv('METRICS_PORT', 9090))
    app.run(host='0.0.0.0', port=port)
