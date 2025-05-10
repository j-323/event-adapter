import json
from jsonschema import validate, ValidationError

from music_adapter.config.settings import get_settings

settings = get_settings()
_schema = None

def _load_schema() -> dict:
    global _schema
    if _schema is None:
        with open(settings.SCHEMA_PATH, encoding="utf-8") as f:
            _schema = json.load(f)
    return _schema

def validate_event(event: dict) -> None:
    """
    Проверяет dict события по JSON-схеме.
    Бросает ValidationError или ValueError.
    """
    try:
        validate(instance=event, schema=_load_schema())
    except ValidationError as e:
        raise ValueError(f"Schema validation error: {e.message}")