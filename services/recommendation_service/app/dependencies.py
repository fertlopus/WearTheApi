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


async def get_asset_retriever(settings: Settings = Depends(get_settings)):
    return JsonAssetRetriever(asset_path=settings.ASSETS_PATH)


async def get_llm_handler(settings: Settings = Depends(get_settings)):
    return OpenAIHandler(
        api_key=settings.OPEN_AI_API_KEY,
        model=settings.OPEN_AI_MODEL,
        temperature=settings.OPEN_AI_TEMPERATURE
    )


async def get_cache_handler(settings: Settings = Depends(get_settings)) -> Optional[AsyncRedisCache]:
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True
    )
    return AsyncRedisCache(redis, prefix="rec_service")


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
