import pytest
from music_adapter.broker.broker import Broker

@pytest.mark.asyncio
async def test_broker_init():
    b = Broker()
    assert b._conn is None
    assert b._channel is None

# Нельзя тестировать connect/publish без реального брокера, здесь мы лишь проверяем атрибуты
