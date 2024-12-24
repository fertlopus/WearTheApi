from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import hashlib
from fastapi.encoders import jsonable_encoder
from pydantic.v1.json import pydantic_encoder

from ...schemas.recommendations import OutfitRecommendation, RecommendationResponse
from ...schemas.weather import WeatherConditions
from ...schemas.assets import AssetItem
from ...core.exceptions import RecommendationServiceException
from .retrieval.json_retriever import JsonAssetRetriever
from .llm.base import LLMHandler


logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Orchestrates the recommendation process."""
    def __init__(self, asset_retriever: JsonAssetRetriever, llm_handler: LLMHandler,
                 cache_handler: Optional[Any] = None, max_recommendations: int = 5):
        self.asset_retriever = asset_retriever
        self.llm_handler = llm_handler
        self.cache_handler = cache_handler
        self.max_recommendations = max_recommendations

    async def get_recommendations(self, weather_conditions: WeatherConditions,
                                  user_preferences: Optional[Dict[str, Any]]) -> RecommendationResponse:
        """Generate outfit recommendations based on weather and user preferences."""
        try:
            await self.asset_retriever.initialize()
            print(f"Weather Conditions: {weather_conditions} in the script engine.py")
            print(f"User Preferences: {user_preferences} in the script engine.py")

            # Retrieve suitable assets based on weather conditions
            filtered_assets = await self.asset_retriever.retrieve_assets(
                weather_conditions=weather_conditions,
                filters=user_preferences)

            if not filtered_assets:
                raise RecommendationServiceException("No suitable assets found for the given conditions")

            print(f"Filtered assets {filtered_assets} in the script engine.py")

            # Prepare context for LLM
            assets_json = [item.model_dump_json() for item in filtered_assets]

            context = {
                "weather": weather_conditions.model_dump_json(),
                "assets": assets_json,
                "style_preferences": user_preferences.get("style_preferences", [])
            }

            # Generate recommendations using LLM
            llm_recommendations = await self.llm_handler.generate_recommendations(
                context=context,
                weather_context={}  # TODO: Empty as per future implementation
            )

            # Process and validate recommendations
            recommendations = self._process_llm_recommendations(llm_recommendations)

            # Create response
            response = RecommendationResponse(
                location=weather_conditions.location,
                recommendations=recommendations[:self.max_recommendations],
                weather_summary=self._generate_weather_summary(weather_conditions),
                style_notes=self._generate_style_notes(recommendations, weather_conditions),
                generated_at=datetime.utcnow()
            )

            # TODO: Cache response if cache handler is available

            return response

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise RecommendationServiceException(str(e))

    async def get_simple_recommendations(self, weather_conditions: WeatherConditions) -> RecommendationResponse:
        try:
            print(f"Weather conditions: {weather_conditions} in script engine.py")
            await self.asset_retriever.initialize()

            filtered_assets = await self.asset_retriever.retrieve_assets_without_filters(weather_conditions=weather_conditions)
            if not filtered_assets:
                raise RecommendationServiceException("No suitable assets found for the given conditions")

            print(f"Len of filtered assets: {len(filtered_assets)} in script engine.py")
            # Prepare context for LLM
            assets_json = [item.model_dump_json() for item in filtered_assets]

            context = {
                "weather": weather_conditions.model_dump_json(),
                "assets": assets_json,
                "style_preferences": []  # Empty for now
            }

            print(f"LLM Context Debug: {context} in script name engine.py")

            # Generate recommendations using LLM
            llm_recommendations = await self.llm_handler.generate_recommendations(
                context=context,
                weather_context={}
            )

            print(f"LLM Recommendations: {llm_recommendations} in script name enginge.py")

            # Process and validate recommendations
            recommendations = self._process_llm_recommendations(llm_recommendations)

            return RecommendationResponse(
                location=weather_conditions.location,
                recommendations=recommendations[:self.max_recommendations],
                weather_summary=self._generate_weather_summary(weather_conditions),
                style_notes=self._generate_style_notes(recommendations, weather_conditions),
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise RecommendationServiceException(str(e))


    def _generate_cache_key(self,weather_conditions: WeatherConditions, user_preferences: Dict[str, Any]) -> str:
        """Generate unique cache key based on input parameters."""
        key_data = f"{weather_conditions.location}_{weather_conditions.temperature}_{user_preferences}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"rec:{key_hash}"

    def _prepare_llm_context(self, assets: List[AssetItem], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for LLM processing."""
        return {
            "assets": [asset.model_dump_json() for asset in assets],
            "style_preferences": user_preferences.get("style", []),
            "gender": user_preferences.get("gender", "unisex"),
            "fit_preference": user_preferences.get("fit", "normal")
        }


    def _process_llm_recommendations(self, llm_output: List[Dict[str, Any]]) -> List[OutfitRecommendation]:
        """Process and validate LLM recommendations."""
        processed_recommendations = []

        for rec_item in llm_output:
            try:
                # Extract the recommendation data (assuming first item in the list)
                rec_data = list(rec_item.values())[0][0]
                description = rec_item.get("description", "Stylish outfit for the weather")
                weather_score = rec_item.get("weather_appropriate_score", 0.0)
                style_score = rec_item.get("style_score", 0.0)

                recommendation = OutfitRecommendation(
                    head=rec_data.get("head", "N/A"),
                    top=rec_data.get("top", "N/A"),
                    bottom=rec_data.get("bottom", "N/A"),
                    footwear=rec_data.get("footwear", "N/A"),
                    description=description,
                    weather_appropriate_score=weather_score,
                    style_score=style_score
                )
                processed_recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Error processing recommendation: {str(e)}")
                continue

        return processed_recommendations

    def _generate_weather_summary(self, weather: WeatherConditions) -> str:
        """Generate a human-readable weather summary."""
        return (
            f"Current weather in {weather.location}: {weather.temperature}°C, "
            f"{weather.description.description}. "
            f"Wind speed: {weather.wind_speed} m/s"
        )

    def _generate_style_notes(self, recommendations: List[OutfitRecommendation], weather: WeatherConditions) -> str:
        """Generate additional style notes based on recommendations and weather."""
        if weather.rain:
            return "Don't forget to grab an umbrella! These outfits are selected to keep you dry and stylish."
        elif weather.snow:
            return "These warm outfits are perfect for snowy conditions. Consider adding a scarf and gloves!"
        elif weather.wind_speed > 5.0:
            return "It's quite windy! These outfits are selected to keep you comfortable in breezy conditions."
        else:
            return "These outfits are perfectly suited for today's weather conditions."
