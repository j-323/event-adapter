import pytest
from music_adapter.core.schema_validator import validate_event
from jsonschema import ValidationError

valid = {
    "id": "1",
    "title": "Song",
    "text": "lyrics",
    "authors": ["A"],
    "metadata": {"platform": "p", "timestamp": "2025-05-10T12:00:00Z"}
}

invalid = {
    "id": "1",
    "title": "Song",
    "text": "lyrics",
    # отсутствуют authors и metadata
}

def test_validate_event_ok():
    validate_event(valid)

def test_validate_event_fail():
    with pytest.raises(ValueError):
        validate_event(invalid)