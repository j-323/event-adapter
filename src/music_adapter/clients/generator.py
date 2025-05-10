from typing import Dict, Any
import logging

from music_adapter.clients.http_client import post_json
from music_adapter.config.settings import get_settings

settings = get_settings()
log = logging.getLogger(__name__)

async def generate(clean_text: str, gen_type: str = "image") -> Dict[str, Any]:
    """
    Вызывает внешний сервис генерации.
    Ожидает: {"url": str, "status": str}
    """
    log.debug("Calling generation service")
    payload = {
        "clean_text": clean_text,
        "type": gen_type
    }
    return await post_json(settings.GENERATION_URL, payload)