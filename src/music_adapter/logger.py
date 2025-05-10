import logging
import sys
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def init_tracer(service_name: str):
    provider = TracerProvider(resource=Resource({SERVICE_NAME: service_name}))
    exporter = OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

def init_logger(name: str, level: int = logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger