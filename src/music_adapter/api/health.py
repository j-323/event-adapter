from aiohttp import web

async def health(request):
    """
    GET /health → {"status": "ok"}
    """
    return web.json_response({"status": "ok"})

def run_health_server(host: str = "0.0.0.0", port: int = None):
    from music_adapter.config.settings import get_settings
    settings = get_settings()
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    loop = runner.loop  # aiohttp internal loop
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port or settings.HEALTH_PORT)
    loop.run_until_complete(site.start())
    print(f"Health endpoint listening on {host}:{port or settings.HEALTH_PORT}")