from aiohttp.abc import HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.openweather import OpenWeatherService
from app.schemas.weather import WeatherResponse, WeatherRequest
from app.dependencies import get_weather_service, get_redis
from app.services.cache_service import WeatherCacheService
from app.config import get_settings
import aioredis
import logging
import traceback

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


@router.post("/weather/proximity", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_proximity(lat: float, lon: float, background_tasks: BackgroundTasks,
                                   weather_cache_service: WeatherCacheService = Depends(get_weather_service)):
    return await weather_cache_service.get_weather_by_proximity(background_tasks, lat, lon)


@router.get("/weather/city/{city}", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_city(city: str, background_tasks: BackgroundTasks,
                               cache_service: WeatherCacheService = Depends(get_weather_service)):
    """Get weather data for a city using caching."""
    return await cache_service.get_weather_by_city(background_tasks, city)


@router.get("/weather/city/{city}/country/{country_code}", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_city_country(city: str, country_code: str, background_tasks: BackgroundTasks,
                                       cache_service: WeatherCacheService = Depends(get_weather_service)):
    """Get weather data for a city and country using caching."""
    return await cache_service.get_weather_by_city_country(background_tasks, city, country_code)
