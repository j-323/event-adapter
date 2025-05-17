# src/music_adapter/core/utils.py
import asyncio
import random
import logging
from typing import Callable, Any, Coroutine
import prometheus_client

async def retry_with_backoff(
    fn: Callable[[], Coroutine[Any, Any, Any]],
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0
) -> Any:
    """
    Retry with exponential backoff and jitter, logging each attempt.
    """
    log = logging.getLogger(__name__)
    attempt = 0
    while True:
        try:
            return await fn()
        except Exception as e:
            if attempt >= retries:
                log.error(f"All {retries} retries failed: {e}")
                raise
            raw = base_delay * (2 ** attempt)
            jitter = raw * 0.2
            delay = min(max_delay, raw + random.uniform(-jitter, jitter))
            log.warning(f"Retry {attempt + 1}/{retries} in {delay:.2f}s after error: {e}")
            await asyncio.sleep(delay)
            attempt += 1

# Prometheus-метрики
REQUEST_LATENCY = prometheus_client.Histogram(
    "adapter_request_latency_seconds",
    "Latency of external requests",
    ["service"]
)
REQUEST_COUNT = prometheus_client.Counter(
    "adapter_request_total",
    "Number of calls to external service",
    ["service", "status"]
)

def record_request(service: str, status: str, latency: float):
    REQUEST_COUNT.labels(service=service, status=status).inc()
    REQUEST_LATENCY.labels(service=service).observe(latency)

def to_dead_letter(msg, reason: str):
    """
    Log and reject message without requeue.
    """
    print(f"DLQ: message {getattr(msg, 'delivery_tag', '<unknown>')}, reason: {reason}")