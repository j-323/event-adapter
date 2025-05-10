import asyncio
from typing import Any, Dict, Callable, Coroutine
import aiohttp
from aiohttp import ClientResponseError

from music_adapter.config.settings import get_settings
from music_adapter.core.utils import retry_with_backoff

settings = get_settings()

async def post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST JSON с retry/backoff, возвращает распарсенный JSON."""
    async def _request() -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=settings.HTTP_TIMEOUT
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    return await retry_with_backoff(_request, retries=3, base_delay=0.5)