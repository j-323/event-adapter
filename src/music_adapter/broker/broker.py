import asyncio
from typing import Callable, Optional, Dict
from aio_pika import connect_robust, IncomingMessage, Message, ExchangeType
from aio_pika.abc import AbstractIncomingMessage

from music_adapter.config.settings import get_settings

settings = get_settings()

class Broker:
    def __init__(self):
        self._conn = None
        self._channel = None

    async def connect(self) -> None:
        """Установить подключение к AMQP-брокеру и создать канал."""
        self._conn = await connect_robust(settings.BROKER_URL)
        self._channel = await self._conn.channel()
        await self._channel.set_qos(prefetch_count=settings.BROKER_PREFETCH)

    async def subscribe(
        self,
        queue_name: str,
        handler: Callable[[AbstractIncomingMessage], None]
    ) -> None:
        """Подписаться на очередь и передать обработчик сообщений."""
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.consume(handler, no_ack=False)

    async def publish(
        self,
        routing_key: str,
        body: bytes,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Опубликовать сообщение в указанный роутинг ключ."""
        exchange = await self._channel.declare_exchange(
            "", ExchangeType.DIRECT
        )
        msg = Message(body, headers=headers or {})
        await exchange.publish(msg, routing_key=routing_key)

    async def close(self) -> None:
        """Закрыть канал и соединение."""
        if self._channel:
            await self._channel.close()
        if self._conn:
            await self._conn.close()