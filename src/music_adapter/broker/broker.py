# src/music_adapter/broker/broker.py
import asyncio
import logging
from typing import Callable, Optional, Dict
from aio_pika import connect_robust, IncomingMessage, Message, ExchangeType
from aio_pika.abc import AbstractIncomingMessage

from music_adapter.config.settings import get_settings
from music_adapter.core.utils import retry_with_backoff

settings = get_settings()
log = logging.getLogger(__name__)

class Broker:
    """
    Подключается к AMQP, умеет retry/backoff при старте,
    автоматически пересоединяется, создаёт DLX и DLQ.
    """
    def __init__(self):
        self._conn = None
        self._channel = None
        self._exchange = None
        self._dlx = "dlx"
        self._dlq = "dlq"

    async def connect(self):
        """Попытаться подключиться с retry/backoff."""
        await retry_with_backoff(self._connect_once, retries=5, base_delay=1.0)

    async def _connect_once(self):
        self._conn = await connect_robust(settings.BROKER_URL)
        self._channel = await self._conn.channel()
        await self._channel.set_qos(prefetch_count=settings.BROKER_PREFETCH)

        # Основной exchange (прямого типа) и DLX + DLQ
        self._exchange = await self._channel.declare_exchange(
            settings.IN_TOPIC + ".exchange", ExchangeType.DIRECT, durable=True
        )
        dlx_ex = await self._channel.declare_exchange(
            self._dlx, ExchangeType.FANOUT, durable=True
        )
        dlq_queue = await self._channel.declare_queue(
            self._dlq, durable=True
        )
        await dlq_queue.bind(dlx_ex)

        log.info("Broker connected, exchange and DLQ declared")

        # Переподписаться на закрытие
        self._conn.add_close_callback(lambda exc: asyncio.create_task(self._on_disconnect(exc)))

    async def _on_disconnect(self, exc):
        log.warning(f"Broker connection closed: {exc}, reconnecting...")
        await asyncio.sleep(2)
        await self.connect()

    async def subscribe(
        self,
        queue_name: str,
        handler: Callable[[AbstractIncomingMessage], None]
    ) -> None:
        """
        Подписаться на очередь с DLX-настройкой.
        Все не ack’нутые месседжи уйдут на DLX.
        """
        # очередь с dead-letter-exchange
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": self._dlx}
        )
        await queue.bind(self._exchange, routing_key=queue_name)
        await queue.consume(handler, no_ack=False)
        log.info(f"Subscribed to queue {queue_name}")

    async def publish(
        self,
        routing_key: str,
        body: bytes,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Публикация в основной exchange.
        """
        msg = Message(body, headers=headers or {})
        await self._exchange.publish(msg, routing_key=routing_key)

    async def publish_dlq(
        self,
        body: bytes,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Явная отправка в DLQ (если нужно).
        """
        dlx_ex = await self._channel.get_exchange(self._dlx)
        msg = Message(body, headers=headers or {})
        await dlx_ex.publish(msg, routing_key="")

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._conn and not self._conn.is_closed:
            await self._conn.close()
        log.info("Broker connection closed cleanly")
