from typing import Dict, Any
import logging

from music_adapter.clients.http_client import post_json
from music_adapter.config.settings import get_settings

settings = get_settings()
log = logging.getLogger(__name__)

async def preprocess(text: str, lang: str = "ru") -> Dict[str, Any]:
    """
    Вызывает внешний сервис предобработки.
    Ожидает: {"clean_text": str, "features": dict}
    """
    log.debug("Calling preprocessor service")
    payload = {
        "text": text,
        "options": {"lang": lang}
    }
    return await post_json(settings.PREPROCESS_URL, payload)