import aioredis
import logging.config
from typing import AsyncGenerator
from fastapi import HTTPException
from app.services.openweather import OpenWeatherService
from app.services.cache_service import WeatherCacheService
from app.config import get_settings
from app.logging_config import setup_logging
from contextlib import asynccontextmanager


# Logging Configuration
logging.config.dictConfig(setup_logging())
logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection (singleton)
# redis = None

async def get_weather_service() -> WeatherCacheService:
    """Provide WeatherCacheService as a dependency."""
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    weather_service = OpenWeatherService()
    return WeatherCacheService(redis, weather_service)


async def get_redis() -> aioredis.Redis:
    """Dependency for Redis"""
    return aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True # returns responses as string rather than bytes that simplifies workflow
        )
