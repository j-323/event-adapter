import pytest
from music_adapter.clients.preprocessor import preprocess

class Dummy:
    called = False
async def dummy_post(url, payload):
    Dummy.called = True
    return {"clean_text": payload["text"].upper(), "features": {}}

@pytest.mark.asyncio
async def test_preprocess(monkeypatch):
    from music_adapter.clients import http_client
    monkeypatch.setattr(http_client, "post_json", dummy_post)
    res = await preprocess("hello", lang="en")
    assert Dummy.called
    assert res["clean_text"] == "HELLO"