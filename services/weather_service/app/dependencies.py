import aioredis
import logging.config
from fastapi import HTTPException
from app.services.openweather import OpenWeatherService
from app.services.cache_service import WeatherCacheService
from app.config import get_settings
from app.logging_config import setup_logging
import re

logging.config.dictConfig(setup_logging())
logger = logging.getLogger(__name__)
settings = get_settings()


def parse_redis_connection_string(conn_str: str) -> str:
    """Parse Azure Redis connection string to Redis URL format"""
    try:
        # Extract host and port
        host_port = conn_str.split(',')[0]
        host, port = host_port.split(':')

        # Extract password
        password_match = re.search(r'password=([^,]+)', conn_str)
        if not password_match:
            raise ValueError("Password not found in connection string")
        password = password_match.group(1)

        # Construct Redis URL
        return f"rediss://default:{password}@{host}:{port}"
    except Exception as e:
        logger.error(f"Failed to parse Redis connection string: {str(e)}")
        raise


async def create_redis_client() -> aioredis.Redis:
    """Create Redis client for Azure Redis Cache"""
    try:
        logger.debug("Creating Redis client for Azure Redis Cache...")

        # Use connection string directly
        redis_url = parse_redis_connection_string(settings.REDIS_PRIMARY_CONNECTION_STRING)
        logger.debug(f"Connecting to Redis using parsed URL")

        return aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,  # Add timeout
            socket_keepalive=True,
            retry_on_timeout=True
        )

    except Exception as e:
        logger.error(f"Failed to create Redis client: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis connection failed with error: {str(e)}")


async def get_weather_service() -> WeatherCacheService:
    """Provide WeatherCacheService as a dependency."""
    try:
        redis = await create_redis_client()
        weather_service = OpenWeatherService()
        return WeatherCacheService(redis, weather_service)
    except Exception as e:
        logger.error(f"Failed to initialise WeatherCacheService due to error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")


async def get_redis() -> aioredis.Redis:
    """Dependency for Redis"""
    try:
        return await create_redis_client()
    except Exception as e:
        logger.error(f"Failed to get Redis client: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redis connection failed: {str(e)}")
