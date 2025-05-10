import asyncio
import random
from typing import Callable, Any, Coroutine
import prometheus_client

# --- Retry с экспоненциальным бэкоффом ---
async def retry_with_backoff(
    fn: Callable[[], Coroutine[Any, Any, Any]],
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0
) -> Any:
    attempt = 0
    while True:
        try:
            return await fn()
        except Exception:
            if attempt >= retries:
                raise
            delay = min(max_delay, base_delay * 2 ** attempt) * (0.8 + random.random() * 0.4)
            await asyncio.sleep(delay)
            attempt += 1

# --- Prometheus-метрики ---
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

# --- Dead-letter helper ---
def to_dead_letter(msg, reason: str):
    # Логируем и отвергаем без повторного закидывания
    print(f"DLQ: message {getattr(msg, 'delivery_tag', '<unknown>')}, reason: {reason}")
    # msg.reject(requeue=False) нужно вызывать отдельно в обработчике