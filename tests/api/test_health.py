import pytest
from aiohttp import web
from music_adapter.api.health import health

@pytest.mark.asyncio
async def test_health_endpoint():
    req = web.Request(
        {},                      # fake app
        {},                      # fake message
        headers={},              # headers
        version=(1,1),
        method="GET",
        rel_url="/health"
    )
    resp = await health(req)
    body = await resp.json()
    assert body == {"status": "ok"}
    assert resp.status == 200