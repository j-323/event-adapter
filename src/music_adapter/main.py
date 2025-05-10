#!/usr/bin/env python3
import asyncio
import signal
import json
import logging
from aio_pika.abc import AbstractIncomingMessage

from music_adapter.config.settings import get_settings
from music_adapter.broker.broker import Broker
from music_adapter.core.schema_validator import validate_event
from music_adapter.clients.preprocessor import preprocess
from music_adapter.clients.generator import generate
from music_adapter.core.utils import to_dead_letter
from music_adapter.logger import init_logger, init_tracer
from music_adapter.api.health import run_health_server

settings = get_settings()
logger = init_logger("music_adapter")
tracer = init_tracer("music_adapter")

class MusicAdapter:
    def __init__(self):
        self.broker = Broker()
        self.shutdown_event = asyncio.Event()

    async def start(self):
        # Запуск health-endpoint
        run_health_server()

        # Подключение к брокеру и подписка
        await self.broker.connect()
        await self.broker.subscribe(settings.IN_TOPIC, self._on_message)
        logger.info(f"Subscribed to {settings.IN_TOPIC}")

        # Обработка сигналов
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.shutdown_event.set)

        logger.info("MusicAdapter is running")
        await self.shutdown_event.wait()
        await self.shutdown()

    async def _on_message(self, msg: AbstractIncomingMessage):
        with tracer.start_as_current_span("handle_message") as span:
            try:
                raw = json.loads(msg.body)
                validate_event(raw)
                span.set_attribute("event.id", raw["id"])

                raw.setdefault("meta", {})["received_at"] = asyncio.get_event_loop().time()

                # Предобработка
                pre_start = asyncio.get_event_loop().time()
                p_res = await preprocess(raw["text"])
                pre_lat = asyncio.get_event_loop().time() - pre_start
                span.set_attribute("preprocessing.duration", pre_lat)

                # Генерация
                gen_start = asyncio.get_event_loop().time()
                g_res = await generate(p_res["clean_text"], raw.get("generate_type", "image"))
                gen_lat = asyncio.get_event_loop().time() - gen_start
                span.set_attribute("generation.duration", gen_lat)

                # Публикация результата
                out_event = {
                    "id": raw["id"],
                    "status": g_res.get("status", "ok"),
                    "artifact_url": g_res["url"],
                    "meta": raw["meta"],
                }
                await self.broker.publish(
                    routing_key=settings.OUT_TOPIC,
                    body=json.dumps(out_event).encode(),
                    headers={"correlation_id": raw["id"]},
                )

                await msg.ack()
                logger.info(f"Event {raw['id']} processed in {pre_lat + gen_lat:.2f}s")

            except Exception as e:
                logger.error("Failed to process message", exc_info=True)
                to_dead_letter(msg, str(e))
                await msg.reject(requeue=False)

    async def shutdown(self):
        logger.info("Shutting down MusicAdapter")
        await self.broker.close()
        # Дать время фоновым задачам завершиться
        await asyncio.sleep(0.1)
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(MusicAdapter().start())
    except KeyboardInterrupt:
        logging.getLogger().info("Interrupted by user, exiting")