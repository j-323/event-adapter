# src/music_adapter/clients/http_client.py
import asyncio
import logging
from typing import Any, Dict
import aiohttp
from aiohttp import ClientError, ClientResponseError
from opentelemetry import trace

from music_adapter.config.settings import get_settings
from music_adapter.core.utils import retry_with_backoff, record_request

settings = get_settings()
tracer = trace.get_tracer(__name__)
log = logging.getLogger(__name__)

class HTTPClient:
    """
    Асинхронный HTTP-клиент с единой aiohttp.Session,
    retry/backoff, метриками и Circuit Breaker.
    """
    def __init__(self):
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.HTTP_TIMEOUT))
        # простейший CB: считаем неудачи подряд
        self._fail_streak = 0
        self._cb_threshold = 5
        self._cb_reset_interval = 60  # сек
        self._last_failure_time = None

    async def post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = url.rsplit("/", 1)[-1] or "http"
        start_ns = trace.time_ns()

        # Circuit Breaker: если слишком много ошибок подряд и мало времени прошло — кидаем сразу
        if self._fail_streak >= self._cb_threshold:
            elapsed = asyncio.get_event_loop().time() - (self._last_failure_time or 0)
            if elapsed < self._cb_reset_interval:
                raise RuntimeError(f"Circuit open for service={service}")
            # иначе сбросить счётчик после таймаута
            self._fail_streak = 0

        async def _do_request():
            async with self._session.post(url, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()

        with tracer.start_as_current_span(f"HTTP POST {service}"):
            try:
                result = await retry_with_backoff(_do_request, retries=3, base_delay=0.5)
                latency = (trace.time_ns() - start_ns) / 1e9
                record_request(service, "success", latency)
                # сброс цепочки неудач
                self._fail_streak = 0
                return result
            except ClientResponseError as e:
                latency = (trace.time_ns() - start_ns) / 1e9
                record_request(service, f"error_{e.status}", latency)
                self._fail_streak += 1
                self._last_failure_time = asyncio.get_event_loop().time()
                log.error(f"HTTP {service} returned {e.status}")
                raise
            except ClientError as e:
                latency = (trace.time_ns() - start_ns) / 1e9
                record_request(service, "client_error", latency)
                self._fail_streak += 1
                self._last_failure_time = asyncio.get_event_loop().time()
                log.error(f"HTTP client error for {service}: {e}")
                raise
            except Exception as e:
                latency = (trace.time_ns() - start_ns) / 1e9
                record_request(service, "error", latency)
                self._fail_streak += 1
                self._last_failure_time = asyncio.get_event_loop().time()
                log.error(f"Unexpected error in HTTPClient.post_json: {e}")
                raise

    async def close(self):
        """Закрыть сессию при shutdown."""
        await self._session.close()
