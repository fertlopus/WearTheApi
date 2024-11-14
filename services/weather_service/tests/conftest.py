import pytest
import aioredis
import asyncio
from fastapi.testclient import TestClient
from typing import Generator
from ..app.main import app
from ..app.dependencies import get_redis


@pytest.fixture
def test_client() -> Generator:
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def redis():
    redis = aioredis.from_url(
        "redis://localhost",
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield redis
    finally:
        await redis.close()
