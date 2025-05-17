# src/music_adapter/clients/http_client.py
import asyncio
from typing import Any, Dict, Callable, Coroutine
import aiohttp
from aiohttp import ClientResponseError
from opentelemetry import trace

from music_adapter.config.settings import get_settings
from music_adapter.core.utils import retry_with_backoff, record_request

settings = get_settings()
tracer = trace.get_tracer(__name__)

async def post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST JSON с retry/backoff, возвращает распарсенный JSON.
    Измеряет latency и записывает метрики.
    """
    service = url.rsplit("/", 1)[-1] or "http"

    async def _request() -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=settings.HTTP_TIMEOUT
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    start = trace.time_ns()
    with tracer.start_as_current_span(f"HTTP POST {service}"):
        try:
            result = await retry_with_backoff(_request, retries=3, base_delay=0.5)
            latency = (trace.time_ns() - start) / 1e9
            record_request(service, "success", latency)
            return result
        except ClientResponseError as e:
            latency = (trace.time_ns() - start) / 1e9
            record_request(service, f"error_{e.status}", latency)
            raise
        except Exception:
            latency = (trace.time_ns() - start) / 1e9
            record_request(service, "error", latency)
            raise
