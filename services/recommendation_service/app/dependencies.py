from functools import lru_cache
from typing import Optional
from fastapi import Depends
from pathlib import Path
from .config import Settings, get_settings
from .services.recommendation_kernel.engine import RecommendationEngine
from .services.recommendation_kernel.retrieval.json_retriever import JsonAssetRetriever
from .services.recommendation_kernel.llm.openai_handler import OpenAIHandler
from .services.weather_client import WeatherClient
from .utils.redis_cache import AsyncRedisCache


@lru_cache()
def get_asset_retriever(settings: Settings = Depends(get_settings)):
    """Get the JSON asset retriever instance."""
    return JsonAssetRetriever(assets_path=Path(settings.ASSETS_PATH))


@lru_cache()
def get_llm_handler(settings: Settings = Depends(get_settings)):
    """Get the LLM handler instance."""
    return OpenAIHandler(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE
    )

@lru_cache()
def get_cache_handler(settings: Settings = Depends(get_settings)) -> Optional[AsyncRedisCache]:
    """Get the cache handler instance."""
    if settings.REDIS_URL:
        return AsyncRedisCache(
            redis_url=settings.REDIS_URL,
            prefix="rec_service"
        )
    return None

@lru_cache()
def get_weather_client(settings: Settings = Depends(get_settings)):
    """Get the weather client instance."""
    return WeatherClient(
        base_url=settings.WEATHER_SERVICE_URL,
        timeout=settings.WEATHER_SERVICE_TIMEOUT
    )

@lru_cache()
def get_recommendation_engine(
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
        cache_handler=cache_handler,
        max_recommendations=settings.MAX_RECOMMENDATIONS
    )
    engine.weather_client = weather_client
    return engine
