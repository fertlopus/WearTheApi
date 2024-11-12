from fastapi import APIRouter, Path, Depends
from fastapi.exceptions import HTTPException
from ...services.openweather import OpenWeatherService
from ...schemas.weather import WeatherResponse, WeatherRequest
from ...dependencies import get_weather_service, get_redis
from ...config import get_settings
import aioredis
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "Service' status OK"}


@router.post("/weather/by_location")
async def get_weather(request: WeatherRequest,
                      weather_service: OpenWeatherService = Depends(get_weather_service),
                      redis: aioredis.Redis = Depends(get_redis)):
    """Get current weather for location"""
    cache_key = f"weather:city:{request.city.lower()}"
    if request.country_code:
        cache_key += f":{request.country_code.lower()}"

    # Try to get from cache
    cached_data = await redis.get(cache_key)

    if cached_data:
        logger.info(f"Cache hit for {cache_key.capitalize()}")
        return WeatherResponse(**json.loads(cached_data))

    # Get fresh data
    logger.info(f"Cache miss for {cache_key.capitalize()}")
    try:
        weather_data = await weather_service.get_current_weather(
            city=request.city,
            country_code=request.country_code
        )
    except Exception as e:
        logger.error(f"Failed to retrieve weather data: {e}")
        raise HTTPException(status_code=503, detail="Weather service temporarily unavailable")

    # Cache results
    await redis.set(
        cache_key,
        weather_data.model_dump_json(),
        ex=settings.WEATHER_CACHE_EXPIRATION
    )
    logger.info(f"Cached new data for {cache_key}")

    return weather_data


@router.post("/weather/by_coordinates", response_model=WeatherResponse)
async def get_weather_by_coordinates(
    latitude: float,
    longitude: float,
    weather_service: OpenWeatherService = Depends(get_weather_service),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get current weather by latitude and longitude"""
    # TODO: Think about different cache key as if the users will have minor changes in lon/lat it will be different
    # cached results for the same location and the outcome will be a lot of request for the same data to the API
    cache_key = f"weather:coords:{latitude}:{longitude}"

    # Try to retrieve cached data
    cached_data = await redis.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return WeatherResponse(**json.loads(cached_data))

    # Fetch fresh data from the weather service
    try:
        weather_data = await weather_service.get_current_weather_by_coordinates(
            latitude=latitude,
            longitude=longitude
        )
    except Exception as e:
        logger.error(f"Failed to retrieve weather data: {e}")
        raise HTTPException(status_code=503, detail="Weather service temporarily unavailable")

    # Cache the response
    await redis.set(
        cache_key,
        weather_data.model_dump_json(),
        ex=settings.WEATHER_CACHE_EXPIRATION
    )
    logger.info(f"Cached new data for {cache_key}")

    return weather_data
