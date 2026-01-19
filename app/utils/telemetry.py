"""
OpenTelemetry instrumentation for LangChain agent
Exports traces to Grafana Tempo via OTLP
"""

import os
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace import Status, StatusCode
import time


class TelemetryManager:
    """Manage OpenTelemetry instrumentation for the travel agent"""
    
    def __init__(
        self,
        service_name: str = "travel-agent",
        service_version: str = "1.0.0",
        otlp_endpoint: Optional[str] = None,
        enable_console_export: bool = False
    ):
        """
        Initialize OpenTelemetry instrumentation
        
        Args:
            service_name: Service name for telemetry
            service_version: Service version
            otlp_endpoint: OTLP gRPC endpoint (default: localhost:4317)
            enable_console_export: Enable console exporter for debugging
        """
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        
        # Create resource with service info
        self.resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Setup tracing
        self._setup_tracing(enable_console_export)
        
        # Setup metrics
        self._setup_metrics()
        
        # Get tracer and meter
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self._create_metrics()
        
        # Auto-instrument requests
        RequestsInstrumentor().instrument()
    
    def _setup_tracing(self, enable_console: bool = False):
        """Setup trace provider and exporters"""
        provider = TracerProvider(resource=self.resource)
        
        # OTLP exporter for Grafana Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.otlp_endpoint,
            insecure=True  # Use TLS in production
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Console exporter for debugging
        if enable_console:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
        trace.set_tracer_provider(provider)
    
    def _setup_metrics(self):
        """Setup metrics provider and exporters"""
        # OTLP exporter for Grafana Mimir/Prometheus
        otlp_metric_exporter = OTLPMetricExporter(
            endpoint=self.otlp_endpoint,
            insecure=True
        )
        
        reader = PeriodicExportingMetricReader(
            otlp_metric_exporter,
            export_interval_millis=10000  # Export every 10s
        )
        
        provider = MeterProvider(
            resource=self.resource,
            metric_readers=[reader]
        )
        metrics.set_meter_provider(provider)
    
    def _create_metrics(self):
        """Create custom metrics for the agent"""
        # Counter for LLM calls
        self.llm_calls_counter = self.meter.create_counter(
            name="agent.llm.calls",
            description="Number of LLM API calls",
            unit="1"
        )
        
        # Histogram for LLM latency
        self.llm_latency_histogram = self.meter.create_histogram(
            name="agent.llm.latency",
            description="LLM API call latency",
            unit="ms"
        )
        
        # Counter for tool calls
        self.tool_calls_counter = self.meter.create_counter(
            name="agent.tool.calls",
            description="Number of tool calls",
            unit="1"
        )
        
        # Histogram for tool latency
        self.tool_latency_histogram = self.meter.create_histogram(
            name="agent.tool.latency",
            description="Tool call latency",
            unit="ms"
        )
        
        # Counter for agent iterations
        self.iterations_counter = self.meter.create_counter(
            name="agent.iterations",
            description="Number of agent iterations",
            unit="1"
        )
        
        # Counter for errors
        self.errors_counter = self.meter.create_counter(
            name="agent.errors",
            description="Number of errors",
            unit="1"
        )
    
    def trace_llm_call(self, model: str, provider: str):
        """
        Context manager for tracing LLM calls
        
        Usage:
            with telemetry.trace_llm_call("claude-sonnet-4", "anthropic") as span:
                response = llm.invoke(messages)
                span.set_attribute("llm.response_tokens", len(response))
        """
        span = self.tracer.start_span(
            "llm.call",
            attributes={
                "llm.model": model,
                "llm.provider": provider,
            }
        )
        
        return LLMSpanContext(span, self)
    
    def trace_tool_call(self, tool_name: str):
        """
        Context manager for tracing tool calls
        
        Usage:
            with telemetry.trace_tool_call("search_flights") as span:
                result = tool.invoke(input)
                span.set_attribute("tool.result_count", len(result))
        """
        span = self.tracer.start_span(
            "tool.call",
            attributes={
                "tool.name": tool_name,
            }
        )
        
        return ToolSpanContext(span, self)
    
    def trace_agent_iteration(self, iteration: int):
        """
        Context manager for tracing agent iterations
        
        Usage:
            with telemetry.trace_agent_iteration(1) as span:
                response = agent.step()
        """
        span = self.tracer.start_span(
            "agent.iteration",
            attributes={
                "agent.iteration": iteration,
            }
        )
        
        return AgentSpanContext(span, self)
    
    def record_llm_call(self, model: str, provider: str, latency_ms: float, tokens: int = 0):
        """Record LLM call metrics"""
        self.llm_calls_counter.add(
            1,
            attributes={
                "llm.model": model,
                "llm.provider": provider
            }
        )
        self.llm_latency_histogram.record(
            latency_ms,
            attributes={
                "llm.model": model,
                "llm.provider": provider
            }
        )
    
    def record_tool_call(self, tool_name: str, latency_ms: float, success: bool):
        """Record tool call metrics"""
        self.tool_calls_counter.add(
            1,
            attributes={
                "tool.name": tool_name,
                "tool.success": str(success).lower()
            }
        )
        self.tool_latency_histogram.record(
            latency_ms,
            attributes={
                "tool.name": tool_name,
                "tool.success": str(success).lower()
            }
        )
    
    def record_error(self, error_type: str, operation: str):
        """Record error metrics"""
        self.errors_counter.add(
            1,
            attributes={
                "error.type": error_type,
                "error.operation": operation
            }
        )


class LLMSpanContext:
    """Context manager for LLM call spans"""
    
    def __init__(self, span, telemetry: TelemetryManager):
        self.span = span
        self.telemetry = telemetry
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
            self.telemetry.record_error(exc_type.__name__, "llm.call")
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.set_attribute("llm.latency_ms", latency_ms)
        self.span.end()


class ToolSpanContext:
    """Context manager for tool call spans"""
    
    def __init__(self, span, telemetry: TelemetryManager):
        self.span = span
        self.telemetry = telemetry
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        
        tool_name = self.span.attributes.get("tool.name", "unknown")
        self.telemetry.record_tool_call(tool_name, latency_ms, success)
        
        if exc_type is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
            self.telemetry.record_error(exc_type.__name__, f"tool.{tool_name}")
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.set_attribute("tool.latency_ms", latency_ms)
        self.span.end()


class AgentSpanContext:
    """Context manager for agent iteration spans"""
    
    def __init__(self, span, telemetry: TelemetryManager):
        self.span = span
        self.telemetry = telemetry
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        
        self.telemetry.iterations_counter.add(1)
        
        if exc_type is not None:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
            self.telemetry.record_error(exc_type.__name__, "agent.iteration")
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.set_attribute("agent.latency_ms", latency_ms)
        self.span.end()


# Global telemetry instance
_telemetry: Optional[TelemetryManager] = None


def init_telemetry(
    service_name: str = "travel-agent",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_console_export: bool = False
) -> TelemetryManager:
    """
    Initialize global telemetry (idempotent - returns existing instance if already initialized)
    
    Usage:
        from utils.telemetry import init_telemetry
        telemetry = init_telemetry()
    """
    global _telemetry
    
    # Si déjà initialisé, retourner l'instance existante
    if _telemetry is not None:
        return _telemetry
    
    _telemetry = TelemetryManager(
        service_name=service_name,
        service_version=service_version,
        otlp_endpoint=otlp_endpoint,
        enable_console_export=enable_console_export
    )
    return _telemetry


def get_telemetry() -> Optional[TelemetryManager]:
    """Get global telemetry instance"""
    return _telemetry
