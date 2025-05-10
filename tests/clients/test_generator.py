import pytest
from music_adapter.clients.generator import generate

async def dummy_post(url, payload):
    return {"url": "http://img", "status": "ok"}

@pytest.mark.asyncio
async def test_generate(monkeypatch):
    from music_adapter.clients import http_client
    monkeypatch.setattr(http_client, "post_json", dummy_post)
    res = await generate("text", gen_type="mp4")
    assert res["url"] == "http://img"
    assert res["status"] == "ok"