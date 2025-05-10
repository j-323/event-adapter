import pytest
import asyncio
from music_adapter.core.utils import retry_with_backoff

counter = {"calls": 0}

async def sometimes():
    counter["calls"] += 1
    if counter["calls"] < 2:
        raise RuntimeError("fail")
    return "ok"

@pytest.mark.asyncio
async def test_retry_success():
    counter["calls"] = 0
    res = await retry_with_backoff(sometimes, retries=3, base_delay=0)
    assert res == "ok"
    assert counter["calls"] == 2

@pytest.mark.asyncio
async def test_retry_exhaust():
    async def always_fail():
        raise RuntimeError
    with pytest.raises(RuntimeError):
        await retry_with_backoff(always_fail, retries=1, base_delay=0)