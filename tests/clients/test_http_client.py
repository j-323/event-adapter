import pytest
import asyncio
from aiohttp import web
from music_adapter.clients.http_client import post_json

@pytest.mark.asyncio
async def test_post_json_success(aiohttp_unused_port, aiohttp_server):
    async def handler(request):
        return web.json_response({"ok": True})
    app = web.Application()
    app.router.add_post("/", handler)
    server = await aiohttp_server(app)
    url = f"http://{server.host}:{server.port}/"
    result = await post_json(url, {"foo": "bar"})
    assert result == {"ok": True}

@pytest.mark.asyncio
async def test_post_json_failure(aiohttp_unused_port):
    # Некорректный URL → должно выбросить
    with pytest.raises(Exception):
        await post_json("http://invalid/", {})