import asyncio
import json
import logging

import aioredis
from typing import Optional
from datetime import datetime
from fastapi import BackgroundTasks
from pydantic import BaseModel
from app.services.openweather import OpenWeatherService
from app.schemas.weather import WeatherResponse
from app.core.exceptions import WeatherServiceException


logger = logging.getLogger(__name__)


class LocationCache(BaseModel):
    """Location Cache Metadata Model"""
    location_key: str
    last_updated: datetime
    active: bool = True
    request_count: int = 0


class WeatherCacheService:
    """Service for managing weather data caching"""
    def __init__(self, redis: aioredis.Redis, weather_service: OpenWeatherService,
                 cache_duration: int = 14400, refresh_threshold: int = 13200):
        """
        Init params
        :param redis: Redis service
        :param weather_service: Weather Service
        :param cache_duration: cache duration in seconds, e.g. 14400 default parameter ~ 4 hours
        :param refresh_threshold: refresh time in seconds, e.g. 13200 default parameter ~ 3.5 hours
        """
        self.redis = redis
        self.weather_service = weather_service
        self.cache_duration = cache_duration
        self.refresh_threshold = refresh_threshold
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

    async def get_weather(self, background_tasks: BackgroundTasks,
                          city: str,
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
