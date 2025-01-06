from typing import Optional
from pathlib import Path

import aioredis
from fastapi import Depends
from app.config import Settings, get_settings
from app.services.recommendation_kernel.engine import RecommendationEngine
from app.services.recommendation_kernel.retrieval.json_retriever import JsonAssetRetriever
from app.services.recommendation_kernel.llm.openai_handler import OpenAIHandler
from app.services.weather_client import WeatherClient
from app.utils.redis_cache import AsyncRedisCache
from openai import api_version
import re
import logging

logger = logging.getLogger(__name__)


async def get_asset_retriever(settings: Settings = Depends(get_settings)):
    return JsonAssetRetriever(asset_path=settings.ASSETS_PATH)


async def get_llm_handler(settings: Settings = Depends(get_settings)):
    return OpenAIHandler(
        api_key=settings.OPEN_AI_API_KEY,
        model=settings.OPEN_AI_MODEL,
        temperature=settings.OPEN_AI_TEMPERATURE,
        api_version="2024-10-01-preview"
    )


async def get_cache_handler(settings: Settings = Depends(get_settings)) -> Optional[AsyncRedisCache]:
    try:
        # Extract host and port
        host_port = settings.REDIS_PRIMARY_CONNECTION_STRING.split(',')[0]
        host, port = host_port.split(':')

        # Extract password
        password_match = re.search(r'password=([^,]+)', settings.REDIS_PRIMARY_CONNECTION_STRING)
        if not password_match:
            raise ValueError("Password not found in connection string")
        password = password_match.group(1)

        # Construct Redis URL
        return AsyncRedisCache(f"rediss://default:{password}@{host}:{port}", prefix="rec_service")
    except Exception as e:
        logger.error(f"Failed to parse Redis connection string: {str(e)}")
        raise


async def get_weather_client(settings: Settings = Depends(get_settings)):
    return WeatherClient(
        base_url=settings.WEATHER_SERVICE_URL,
        timeout=settings.WEATHER_SERVICE_TIMEOUT
    )


async def get_recommendation_engine(
    asset_retriever: JsonAssetRetriever = Depends(get_asset_retriever),
    llm_handler: OpenAIHandler = Depends(get_llm_handler),
    cache_handler: Optional[AsyncRedisCache] = Depends(get_cache_handler),
    weather_client: WeatherClient = Depends(get_weather_client),
    settings: Settings = Depends(get_settings)
) -> RecommendationEngine:
    """Get the recommendation engine instance."""
    engine = RecommendationEngine(
        asset_retriever=asset_retriever,
        llm_handler=llm_handler,
        cache_handler=cache_handler
    )
    engine.weather_client = weather_client
    return engine
