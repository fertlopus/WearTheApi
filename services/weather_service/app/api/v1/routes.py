from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.openweather import OpenWeatherService
from app.schemas.weather import WeatherResponse, WeatherRequest
from app.dependencies import get_weather_service, get_redis
from app.services.cache_service import WeatherCacheService
from app.config import get_settings
import aioredis
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "Service' status OK"}


async def get_cache_service(weather_service: OpenWeatherService = Depends(get_weather_service),
                            redis: aioredis.Redis = Depends(get_redis)) -> WeatherCacheService:
    """Dependency for weather cache service"""
    return WeatherCacheService(redis, weather_service)


@router.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest,
                      background_tasks: BackgroundTasks,
                      cache_service: WeatherCacheService = Depends(get_cache_service)):
    """Get current weather for a location with smart caching mechanism"""
    return await cache_service.get_weather(
        background_tasks,
        request.city,
        request.country_code
    )
