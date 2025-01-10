from fastapi.exceptions import HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks
from app.services.openweather import OpenWeatherService
from app.schemas.weather import WeatherResponse, WeatherRequest
from app.schemas.forecast import ForecastResponse
from app.dependencies import get_weather_service, get_redis
from app.services.cache_service import WeatherCacheService
from app.config import get_settings

import aioredis
import logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check triggered.")
    return {"status": "Service' status OK"}


async def get_cache_service(weather_service: OpenWeatherService = Depends(get_weather_service),
                            redis: aioredis.Redis = Depends(get_redis)) -> WeatherCacheService:
    """Dependency for weather cache service"""
    logger.info("get_cache_service triggered and returned the cache service.")
    try:
        return WeatherCacheService(redis, weather_service)
    except Exception as e:
        logger.error(f"Error in forming the get_cache_service: {str(e)}")
        return HTTPException(status_code=500, detail="Failed to get/form cache service")


@router.post("/weather/proximity", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_proximity(lat: float, lon: float, background_tasks: BackgroundTasks,
                                   weather_cache_service: WeatherCacheService = Depends(get_weather_service)):
    try:
        logger.info("The endpoint /weather/proximity has been triggered successfully")
        return await weather_cache_service.get_weather_by_proximity(background_tasks, lat, lon)
    except Exception as e:
        logger.error(f"The endpoint /weather/proximity failed with error: {str(e)}")
        return HTTPException(status_code=500, detail="Failed to trigger get_weather_by_proximity endpoint")


@router.get("/weather/city/{city}", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_city(city: str, background_tasks: BackgroundTasks,
                               cache_service: WeatherCacheService = Depends(get_weather_service)):
    """Get weather data for a city using caching."""
    try:
        logger.info(f"The endpoint /weather/city/{city} has been triggered")
        return await cache_service.get_weather_by_city(background_tasks, city)
    except Exception as e:
        logger.error(f"The endpoint /weather/city/{city} with error: {str(e)}")
        return HTTPException(status_code=500, detail="Failed to trigger endpoint /weather/city/{city}")


@router.get("/weather/city/{city}/country/{country_code}", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_by_city_country(city: str, country_code: str, background_tasks: BackgroundTasks,
                                       cache_service: WeatherCacheService = Depends(get_weather_service)):
    """Get weather data for a city and country using caching."""
    try:
        logger.info(f"The endpoint /weather/city/{city}/country/{country_code} has been triggered")
        return await cache_service.get_weather_by_city_country(background_tasks, city, country_code)
    except Exception as e:
        logger.error(f"The endpoint /weather/city/{city}/country/{country_code} with error: {str(e)}")
        return HTTPException(status_code=500,
                             detail="Failed to trigger endpoint /weather/city/{city}/country/{country_code}")


@router.get("/weather/city/{city}/forecast", response_model=ForecastResponse, tags=["Weather"])
async def get_city_forecast(city: str, background_tasks: BackgroundTasks, country_code: Optional[str] = None,
                            cache_service: WeatherCacheService = Depends(get_weather_service)) -> ForecastResponse:
    try:
        logger.info(f"The endpoint /weather/city/{city}/forecast has been triggered")
        return await cache_service.get_forecast_by_city(background_tasks, city, country_code)
    except Exception as e:
        logger.error(f"The endpoint /weather/city/{city}/forecast with error: {str(e)}")
        return HTTPException(status_code=500,
                             detail="Failed to trigger endpoint /weather/city/{city}/forecast")
