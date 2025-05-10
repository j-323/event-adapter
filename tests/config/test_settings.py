import os
import pytest
from music_adapter.config.settings import get_settings, Settings

def test_settings_load(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BROKER_URL=amqp://user:pass@host/\n"
        "PREPROCESS_URL=http://preproc/\n"
        "GENERATION_URL=http://gen/\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BROKER_URL", "amqp://override/")
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.BROKER_URL == "amqp://override/"
    assert s.PREPROCESS_URL == "http://preproc/"
    assert s.GENERATION_URL == "http://gen/"