import aioredis
import logging.config
from typing import AsyncGenerator
from fastapi import HTTPException
from app.services.openweather import OpenWeatherService
from app.config import get_settings
from app.logging_config import setup_logging
from contextlib import asynccontextmanager


# Logging Configuration
logging.config.dictConfig(setup_logging())
logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection (singleton)
# redis = None

async def get_weather_service() -> AsyncGenerator[OpenWeatherService, None]:
    """Dependency for weather service"""
    try:
        service = OpenWeatherService()
        return service
    except Exception as e:
        logger.error(f"Failed to initialize WeatherService: {str(e)}")
        raise HTTPException(status_code=503, detail="Weather service is unavailable.")


async def get_redis() -> aioredis.Redis:
    """Dependency for Redis"""
    return aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True # returns responses as string rather than bytes that simplifies workflow
        )
