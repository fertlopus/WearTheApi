import asyncio
import json
import logging
from math import radians, cos, sin, sqrt, atan2
import aioredis
from typing import Optional
from datetime import datetime
from fastapi import BackgroundTasks
from pydantic import BaseModel
from app.services.openweather import OpenWeatherService
from app.schemas.weather import WeatherResponse
from app.core.exceptions import WeatherServiceException
from app.schemas.forecast import ForecastResponse


logger = logging.getLogger(__name__)


class LocationCache(BaseModel):
    """Location Cache Metadata Model"""
    location_key: str
    last_updated: datetime
    active: bool = True
    request_count: int = 0


def haversine(lat1, lon1, lat2, lon2):
    """Calculates the great-circle distance between two points on the Earth using the Haversine formula"""
    # Constant radius of the Earth in kilometers
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_proximity_key(lat: float, lon: float, precision: float = 1.0) -> str:
    """
    Generate a cache key based on proximity clustering

    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        precision (float): Precision of clustering in km

    Returns:
        str: Cache key for the proximity cluster
    """
    lat_cluster = round(lat / precision) * precision
    lon_cluster = round(lon / precision) * precision
    return f"weather:proximity:{lat_cluster:.2f}:{lon_cluster:.2f}"


class WeatherCacheService:
    """Service for managing weather data caching"""
    def __init__(self, redis: aioredis.Redis, weather_service: OpenWeatherService,
                 cache_duration: int = 14400, refresh_threshold: int = 13200, proximity_precision: float = 5.0):
        self.redis = redis
        self.weather_service = weather_service
        self.cache_duration = cache_duration
        self.refresh_threshold = refresh_threshold
        self.proximity_precision = proximity_precision
        self._background_task: Optional[asyncio.Task] = None

    async def start_background_task(self):
        """Start background refresh task"""
        if not self._background_task or self._background_task.done():
            self._background_task = asyncio.create_task(self._refresh_loop())
            logger.info("Started background refresh task")

    async def stop_background_refresh(self):
        """Stop background refresh task"""
        if self._background_task and not self._background_task.done():
            logger.info("Stopping the background task")
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError as e:
                logger.info(f"Error in stopping background task: {str(e)}")
            logger.info("Stopped the background task")

    def _get_cache_key(self, city: str, country_code: Optional[str]=None) -> str:
        """Generate cache key for location"""
        logger.info(f"Generated the cache key for the city: {city.capitalize()}")
        return f"weather:{city.lower()}" + (f":{country_code.lower()}" if country_code else "")

    def _get_metadata_key(self, cache_key: str) -> str:
        """Generate metadata key for cache entry"""
        logger.info(f"Generating the metadata key for the cache entry.")
        return f"metadata:{cache_key}"

    async def get_weather(self, background_tasks: BackgroundTasks, city: str,
                          country_code: Optional[str]=None) -> WeatherResponse:
        """Get weather data with smart caching mechanism"""
        cache_key = self._get_cache_key(city, country_code)
        metadata_key = self._get_metadata_key(cache_key)

        # Try to get the cached data if any
        cached_data = await self.redis.get(cache_key)
        metadata_data = await self.redis.get(metadata_key)

        if cached_data:
            weather_data = WeatherResponse(**json.load(cached_data))
            metadata_ = LocationCache(**json.loads(metadata_data)) if metadata_data else None
            # Update the counter for the request
            if metadata_:
                metadata_.request_count += 1
                await self.redis.set(
                    metadata_key,
                    metadata_.model_dump_json(),
                    ex=self.cache_duration
                )
            # Check the need of the refresh process
            if metadata_ and (datetime.now() - metadata_.last_updated).total_seconds() > self.refresh_threshold:
                background_tasks.add_task(self._refresh_cache, city, country_code)

            return weather_data
        # If no cached data, fetch and cache
        return await self._fetch_and_cache(city, country_code)

    async def _fetch_and_cache(self, city: str, country_code: Optional[str]=None) -> WeatherResponse:
        """Fetch weather data and cache it"""
        try:
            weather_data = await self.weather_service.get_current_weather(city, country_code)
            cache_key = self._get_cache_key(city, country_code)
            metadata_key = self._get_metadata_key(cache_key)
            metadata = LocationCache(location_key=cache_key, last_updated=datetime.now(), request_count=1)

            # Cache data
            await self.redis.set(cache_key, weather_data.model_dump_json(), ex=self.cache_duration)
            await self.redis.set(metadata_key, metadata.model_dump_json(), ex=self.cache_duration)

            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise WeatherServiceException(str(e))

    async def _refresh_cache(self, city: str, country_code: Optional[str]=None):
        """Refresh cached weather data"""
        try:
            await self._fetch_and_cache(city, country_code)
            logger.info(f"Refreshed cache for {city.capitalize()}")
        except Exception as e:
            logger.error(f"Failed to refresh cache data for {city.capitalize()}: {str(e)}")

    async def _refresh_loop(self):
        """Background task to refresh cached locations"""
        while True:
            try:
                # retrieve all metadata keys
                metadata_keys = await self.redis.keys("metadata:weather:*")
                for metadata_key in metadata_keys:
                    metadata_data = await self.redis.get(metadata_key)
                    if metadata_data:
                        metadata_ = LocationCache(**json.loads(metadata_data))
                        # Refresh is needed?
                        if (datetime.now() - metadata_.last_updated).total_seconds() > self.refresh_threshold:
                            # Extract city/country from cache key
                            _, _, city, *country = metadata_.location_key.split(":")
                            country_code = country[0] if country else None
                            # Refresh cache
                            await self._refresh_cache(city, country_code)
                            # Delay to prevent rate limiting
                            await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in refresh loop: {str(e)}")

            # Wait next refresh cycle ~ 5 minutes
            await asyncio.sleep(300)

    async def get_weather_by_proximity(self, background_tasks: BackgroundTasks, lat: float,
                                       lon: float) -> WeatherResponse:
        """Get weather data by proximity based caching.

        Args:
            background_tasks (BackgroundTasks): FastAPI background tasks for async cache refresh.
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.

        Returns:
            WeatherResponse: Weather data for the location.
        """
        proximity_key = get_proximity_key(lat, lon, self.proximity_precision)
        cached_data = await self.redis.get(proximity_key)

        if cached_data:
            logger.info(f"Cache hit for proximity key: {proximity_key}")
            weather_data = WeatherResponse(**json.loads(cached_data))
            # Schedule background refresh if needed
            if (datetime.now() - datetime.fromtimestamp(weather_data.timestamp)).total_seconds() > self.refresh_threshold:
                background_tasks.add_task(self._refresh_cache_by_proximity, lat, lon)
            return weather_data
        # If not found in cache -> fetch from Weather API and cache the results
        return await self._fetch_and_cache_by_proximity(lat, lon, proximity_key)

    async def get_weather_by_city(self, background_tasks: BackgroundTasks, city: str) -> WeatherResponse:
        """
        Get weather data for a city using caching.

        Args:
            background_tasks (BackgroundTasks): FastAPI background tasks for async cache refresh.
            city (str): City name.

        Returns:
            WeatherResponse: Weather data for the city.
        """
        cache_key = f"weather:city:{city.lower()}"

        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for city key: {cache_key}")
            weather_data = WeatherResponse(**json.loads(cached_data))
            if (datetime.now() - datetime.fromtimestamp(weather_data.timestamp)).total_seconds() > self.refresh_threshold:
                background_tasks.add_task(self._refresh_cache_by_city, city)
            return weather_data

        return await self._fetch_and_cache_by_city(city, cache_key)

    async def get_weather_by_city_country(self, background_tasks: BackgroundTasks, city: str, country_code: str) -> WeatherResponse:
        """
        Get weather data for a city and country using caching.

        Args:
            background_tasks (BackgroundTasks): FastAPI background tasks for async cache refresh.
            city (str): City name.
            country_code (str): ISO country code.

        Returns:
            WeatherResponse: Weather data for the city and country.
        """
        cache_key = f"weather:city:{city.lower()}:{country_code.lower()}"

        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for city-country key: {cache_key}")
            weather_data = WeatherResponse(**json.loads(cached_data))
            if (datetime.now() - datetime.fromtimestamp(weather_data.timestamp)).total_seconds() > self.refresh_threshold:
                background_tasks.add_task(self._refresh_cache_by_city_country, city, country_code)
            return weather_data

        return await self._fetch_and_cache_by_city_country(city, country_code, cache_key)

    async def _fetch_and_cache_by_proximity(self, lat: float, lon: float, proximity_key: str) -> WeatherResponse:
        """
        Fetch weather data from OpenWeather API and cache it under a proximity key.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            proximity_key (str): Proximity cache key.

        Returns:
            WeatherResponse: Weather data fetched from the API.
        """
        try:
            weather_data = await self.weather_service.get_current_weather_by_coordinates(lat, lon)
            await self.redis.set(proximity_key, weather_data.model_dump_json(), ex=self.cache_duration)
            logger.info(f"Cached weather data for proximity key: {proximity_key}")
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather data for proximity key: {proximity_key} - {str(e)}")
            raise WeatherServiceException(str(e))

    async def _fetch_and_cache_by_city(self, city: str, cache_key: str) -> WeatherResponse:
        try:
            weather_data = await self.weather_service.get_current_weather(city)
            await self.redis.set(cache_key, weather_data.model_dump_json(), ex=self.cache_duration)
            logger.info(f"Cached weather data for city key: {cache_key}")
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather data for city key: {cache_key} - {str(e)}")
            raise WeatherServiceException(str(e))

    async def _fetch_and_cache_by_city_country(self, city: str, country_code: str, cache_key: str) -> WeatherResponse:
        try:
            weather_data = await self.weather_service.get_current_weather(city, country_code)
            await self.redis.set(cache_key, weather_data.model_dump_json(), ex=self.cache_duration)
            logger.info(f"Cached weather data for city-country key: {cache_key}")
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather data for city-country key: {cache_key} - {str(e)}")
            raise WeatherServiceException(str(e))

    async def _refresh_cache_by_proximity(self, lat: float, lon: float):
        """
        Refresh the cache entry for a proximity cluster.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
        """
        proximity_key = get_proximity_key(lat, lon, self.proximity_precision)
        await self._fetch_and_cache_by_proximity(lat, lon, proximity_key)

    async def _refresh_cache_by_city(self, city: str):
        cache_key = f"weather:city:{city.lower()}"
        await self._fetch_and_cache_by_city(city, cache_key)

    async def _refresh_cache_by_city_country(self, city: str, country_code: str):
        cache_key = f"weather:city:{city.lower()}:{country_code.lower()}"
        await self._fetch_and_cache_by_city

    async def get_forecast_by_city(self, background_tasks: BackgroundTasks, city: str,
                                   country_code: Optional[str] = None) -> ForecastResponse:
        cache_key = f"forecast:city:{city.lower()}" + (f":{country_code.lower()}" if country_code else "")
        # Try to get cached data
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for forecast key: {cache_key}")
            forecast_data = ForecastResponse(**json.loads(cached_data))
            # Check if refresh is needed
            if (datetime.now() - datetime.fromtimestamp(
                    forecast_data.forecast_points[0].dt)).total_seconds() > self.refresh_threshold:
                background_tasks.add_task(self._refresh_forecast_cache, city, country_code)
            return forecast_data
        # If not in cache, fetch and cache
        return await self._fetch_and_cache_forecast(city, country_code)

    async def _fetch_and_cache_forecast(self, city: str, country_code: Optional[str] = None) -> ForecastResponse:
        try:
            forecast_data = await self.weather_service.get_forecast(city, country_code)
            cache_key = f"forecast:city:{city.lower()}" + (f":{country_code.lower()}" if country_code else "")
            # Cache the forecast data
            await self.redis.set(
                cache_key,
                forecast_data.model_dump_json(),
                ex=self.cache_duration
            )
            logger.info(f"Cached forecast data for key: {cache_key}")
            return forecast_data

        except Exception as e:
            logger.error(f"Error fetching forecast data: {str(e)}")
            raise WeatherServiceException(str(e))

    async def _refresh_forecast_cache(self, city: str, country_code: Optional[str] = None):
        try:
            await self._fetch_and_cache_forecast(city, country_code)
            logger.info(f"Refreshed forecast cache for {city}")
        except Exception as e:
            logger.error(f"Failed to refresh forecast cache for {city}: {str(e)}")
