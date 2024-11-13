import aioredis
import logging.config
from typing import AsyncGenerator
from fastapi import HTTPException
from .services.openweather import OpenWeatherService
from .config import get_settings
from .logging_config import setup_logging
from contextlib import asynccontextmanager


# Logging Configuration
logging.config.dictConfig(setup_logging())
logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection (singleton)
redis = None

@asynccontextmanager
async def get_weather_service() -> AsyncGenerator[OpenWeatherService, None]:
    """Dependency for weather service"""
    service = OpenWeatherService()
    try:
        yield service
    except Exception as e:
        logger.error(f"Failed to initialize WeatherService: {str(e)}")
        raise HTTPException(status_code=503, detail="Weather service is unavailable.")
    finally:
        await service.close()

async def get_redis() -> aioredis.Redis:
    """Dependency for Redis"""
    global redis
    if redis is None:
        redis = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True # returns responses as string rather than bytes that simplifies workflow
        )
    return redis
