from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import hashlib
from ...schemas.recommendations import OutfitRecommendation, RecommendationResponse
from ...schemas.weather import WeatherConditions
from ...schemas.assets import AssetItem
from ...core.exceptions import RecommendationServiceException
from .retrieval.base import BaseRetriever
from .llm.base import LLMHandler


logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Orchestrates the recommendation process."""
    def __init__(self, asset_retriever: BaseRetriever, llm_handler: LLMHandler,
                 cache_handler: Optional[Any] = None, max_recommendations: int = 5):
        self.asset_retriever = asset_retriever
        self.llm_handler = llm_handler
        self.cache_handler = cache_handler
        self.max_recommendations = max_recommendations

    async def get_recommendations(self, weather_conditions: WeatherConditions,
                                  user_preferences: Dict[str, Any]) -> RecommendationResponse:
        """Generate outfit recommendations based on weather and user preferences."""
        try:
            # Check cache if available
            cache_key = self._generate_cache_key(weather_conditions, user_preferences)
            if self.cache_handler:
                cached_response = await self.cache_handler.get(cache_key)
                if cached_response:
                    logger.info("Returning cached recommendations")
                    return cached_response

            # Retrieve suitable assets based on weather conditions
            filtered_assets = await self.asset_retriever.retrieve_assets(
                weather_conditions=weather_conditions,
                filters=user_preferences)

            if not filtered_assets:
                raise RecommendationServiceException("No suitable assets found for the given conditions")

            # Prepare context for LLM
            context = self._prepare_llm_context(filtered_assets, user_preferences)
            weather_context = weather_conditions.__dict__

            # Generate recommendations using LLM
            llm_recommendations = await self.llm_handler.generate_recommendations(context=context,
                                                                                  weather_context=weather_context)

            # Process and validate recommendations
            recommendations = self._process_llm_recommendations(llm_recommendations, filtered_assets)

            # Create response
            response = RecommendationResponse(
                recommendations=recommendations[:self.max_recommendations],
                weather_summary=self._generate_weather_summary(weather_conditions),
                style_notes=self._generate_style_notes(recommendations, weather_conditions),
                generated_at=datetime.utcnow()
            )

            # Cache response if cache handler is available
            if self.cache_handler:
                await self.cache_handler.set(cache_key, response, expire=14400)  # 4 hour cache

            return response

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

    def _process_llm_recommendations(self, llm_output: Dict[str, Any],
                                     available_assets: List[AssetItem]) -> List[OutfitRecommendation]:
        """Process and validate LLM recommendations."""
        available_asset_names = {asset.asset_name for asset in available_assets}
        processed_recommendations = []

        for rec_item in llm_output:
            try:
                # Extract the recommendation data - handle both formats
                rec_key = next(iter(rec_item.keys()))  # e.g., "recommendation_1"
                rec_data = rec_item[rec_key]

                # Handle the nested array structure
                if isinstance(rec_data, list) and len(rec_data) > 0:
                    outfit_data = rec_data[0]
                else:
                    outfit_data = rec_data

                # Validate outfit pieces
                outfit_pieces = {
                    "head": outfit_data.get("head", "N/A"),
                    "top": outfit_data.get("top"),
                    "bottom": outfit_data.get("bottom"),
                    "footwear": outfit_data.get("footwear")
                }

                # Skip if required pieces are missing or not in available assets
                required_pieces = {"top", "bottom", "footwear"}
                for piece in required_pieces:
                    if not outfit_pieces.get(piece) or \
                            (outfit_pieces[piece] != "N/A" and
                             outfit_pieces[piece] not in available_asset_names):
                        logger.warning(
                            f"Missing or invalid required piece {piece} in recommendation"
                        )
                        continue

                # Create recommendation object
                recommendation = OutfitRecommendation(
                    head=None if outfit_pieces["head"] == "N/A" else outfit_pieces["head"],
                    top=outfit_pieces["top"],
                    bottom=outfit_pieces["bottom"],
                    footwear=outfit_pieces["footwear"],
                    description=rec_item.get("description", "Stylish outfit for the weather"),
                    weather_appropriate_score=rec_item.get("weather_appropriate_score", 0.8),
                    style_score=rec_item.get("style_score", 0.8)
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
