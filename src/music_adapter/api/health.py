# src/music_adapter/api/health.py
from aiohttp import web
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

async def health(request):
    """
    Простая проверка здоровья.
    GET /health → {"status": "ok"}
    """
    return web.json_response({"status": "ok"})

async def metrics(request):
    """
    Проброс /metrics для Prometheus.
    """
    data = generate_latest()
    return web.Response(body=data, content_type=CONTENT_TYPE_LATEST)

def run_health_server(host: str = "0.0.0.0", port: int = None):
    from music_adapter.config.settings import get_settings
    settings = get_settings()
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/metrics", metrics)
    runner = web.AppRunner(app)
    loop = runner.loop  # aiohttp internal loop
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port or settings.HEALTH_PORT)
    loop.run_until_complete(site.start())
    print(f"Health endpoint listening on {host}:{port or settings.HEALTH_PORT}")