"""
Configuration centralisée du logging en JSON pour ingestion Prometheus
Format structuré avec métriques et traces
"""

import logging
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, REGISTRY, CollectorRegistry
import time


# ============================================================================
# MÉTRIQUES PROMETHEUS (avec vérification pour éviter duplication Streamlit)
# ============================================================================

def _metric_exists(name):
    """Check if a metric already exists in the registry"""
    try:
        # Check in the collector_to_names mapping
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return True
        # Also check by iterating registered names (handles _total, _created variants)
        for collector, names in REGISTRY._collector_to_names.items():
            if name in names or any(n.startswith(name) for n in names):
                return True
    except:
        pass
    return False

def _find_metric(name):
    """Find and return existing metric by name"""
    try:
        # Direct lookup first
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        # Check for base name match (handles _total suffix for Counters)
        for collector, names in REGISTRY._collector_to_names.items():
            if name in names or any(n.startswith(name) for n in names):
                return collector
    except:
        pass
    return None

def get_or_create_counter(name, description, labelnames):
    """Get existing counter or create new one"""
    existing = _find_metric(name)
    if existing:
        return existing
    return Counter(name, description, labelnames)

def get_or_create_histogram(name, description, labelnames):
    """Get existing histogram or create new one"""
    existing = _find_metric(name)
    if existing:
        return existing
    return Histogram(name, description, labelnames)

def get_or_create_gauge(name, description):
    """Get existing gauge or create new one"""
    existing = _find_metric(name)
    if existing:
        return existing
    return Gauge(name, description)

# Compteurs d'événements
log_counter = get_or_create_counter(
    'app_log_messages_total',
    'Total number of log messages',
    ['level', 'module']
)

api_calls_counter = get_or_create_counter(
    'api_calls_total',
    'Total number of API calls',
    ['service', 'status']
)

# Histogrammes de latence
api_latency = get_or_create_histogram(
    'api_call_duration_seconds',
    'API call latency in seconds',
    ['service']
)

llm_latency = get_or_create_histogram(
    'llm_call_duration_seconds',
    'LLM call latency in seconds',
    ['model']
)

# Jauges (valeurs instantanées)
active_requests = get_or_create_gauge(
    'active_requests',
    'Number of active requests'
)

agent_iterations = get_or_create_gauge(
    'agent_iterations_current',
    'Current agent iteration count'
)


# ============================================================================
# CUSTOM JSON FORMATTER
# ============================================================================

class PrometheusJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter JSON enrichi avec des champs pour Prometheus
    """
    
    def add_fields(self, log_record, record, message_dict):
        """Ajouter des champs personnalisés au log JSON"""
        super().add_fields(log_record, record, message_dict)
        
        # Timestamp ISO 8601 (format Prometheus)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Niveau de log
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Source
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Labels Prometheus
        log_record['labels'] = {
            'environment': 'production',
            'service': 'travel-agent',
            'version': '1.0.0'
        }
        
        # Incrémente le compteur Prometheus
        log_counter.labels(level=log_record['level'], module=record.module).inc()


# ============================================================================
# CONFIGURATION DU LOGGER
# ============================================================================

def setup_json_logging(
    level: str = "INFO",
    log_file: str = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure le logging JSON pour l'application
    
    Args:
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin vers le fichier de log (optionnel)
        console_output: Afficher les logs dans la console
        
    Returns:
        Logger configuré
    """
    # Formatter JSON (sans rename_fields pour éviter les conflits)
    formatter = PrometheusJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(line)d %(message)s'
    )
    
    # Handler console (stdout)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
    
    # Handler fichier (optionnel)
    handlers = []
    if console_output:
        handlers.append(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configuration du root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True  # Override configuration existante
    )
    
    # Désactiver les logs verbeux de bibliothèques tierces
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


# ============================================================================
# LOGGER APPLICATIF AVEC CONTEXTE
# ============================================================================

class ContextLogger:
    """
    Logger enrichi avec contexte métier et métriques
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Ajouter du contexte aux logs suivants"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Nettoyer le contexte"""
        self.context = {}
    
    def _log(self, level, message, **extra):
        """Log avec contexte enrichi"""
        log_data = {**self.context, **extra}
        getattr(self.logger, level)(message, extra=log_data)
    
    def debug(self, message, **extra):
        self._log('debug', message, **extra)
    
    def info(self, message, **extra):
        self._log('info', message, **extra)
    
    def warning(self, message, **extra):
        self._log('warning', message, **extra)
    
    def error(self, message, **extra):
        self._log('error', message, **extra)
    
    def critical(self, message, **extra):
        self._log('critical', message, **extra)
    
    # ========================================================================
    # MÉTHODES SPÉCIFIQUES MÉTIER
    # ========================================================================
    
    def log_api_call(self, service: str, status: str, duration: float, **extra):
        """Log d'un appel API avec métriques"""
        api_calls_counter.labels(service=service, status=status).inc()
        api_latency.labels(service=service).observe(duration)
        
        self.info(
            f"API call: {service}",
            service=service,
            status=status,
            duration_seconds=duration,
            **extra
        )
    
    def log_llm_call(self, model: str, duration: float, tokens: int = None, **extra):
        """Log d'un appel LLM avec métriques"""
        llm_latency.labels(model=model).observe(duration)
        
        data = {
            'model': model,
            'duration_seconds': duration,
            **extra
        }
        if tokens:
            data['tokens'] = tokens
        
        self.info(f"LLM call: {model}", **data)
    
    def log_agent_iteration(self, iteration: int, tools_used: list = None, **extra):
        """Log d'une itération d'agent"""
        agent_iterations.set(iteration)
        
        self.info(
            f"Agent iteration {iteration}",
            iteration=iteration,
            tools_used=tools_used or [],
            **extra
        )


# ============================================================================
# DÉCORATEURS POUR MESURES AUTOMATIQUES
# ============================================================================

def log_execution_time(logger: ContextLogger, operation: str):
    """Décorateur pour logger le temps d'exécution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    duration_seconds=duration,
                    status="success"
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration_seconds=duration,
                    status="error",
                    error=str(e)
                )
                raise
        return wrapper
    return decorator


# ============================================================================
# INITIALISATION PAR DÉFAUT
# ============================================================================

# Logger par défaut pour le module
default_logger = setup_json_logging(
    level="INFO",
    log_file="logs/app.json.log",
    console_output=True
)

# Export des fonctions principales
__all__ = [
    'setup_json_logging',
    'ContextLogger',
    'log_execution_time',
    'api_calls_counter',
    'api_latency',
    'llm_latency',
    'active_requests',
    'agent_iterations'
]
