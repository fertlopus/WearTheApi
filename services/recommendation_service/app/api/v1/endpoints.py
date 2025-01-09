from http.client import HTTPException
from typing import Optional, List
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from app.schemas.recommendations import RecommendationResponse
from app.schemas.weather import WeatherConditions
from app.services.recommendation_kernel.engine import RecommendationEngine
from app.dependencies import get_recommendation_engine
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)
router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request model for recommendations"""
    location: str
    preferred_colors: Optional[List[str]] = []
    preferred_styles: Optional[List[str]] = []
    gender: Optional[str] = "unisex"
    fit_preference: Optional[str] = "normal"


@router.post("/recommendations/complex", response_model=RecommendationResponse)
async def get_recommendations_complex(request: RecommendationRequest,
                                      engine: RecommendationEngine = Depends(get_recommendation_engine)) -> RecommendationResponse:
    try:
        logger.debug("Accessing the weather conditions.")
        weather_conditions = await engine.weather_client.get_weather(request.location)
        logger.info(f"The weather conditions obtained: {weather_conditions} for the endpoint called /recommendations/complex")

        logger.info(f"Forming the user preferences.")
        user_preferences = {
            "colors": request.preferred_colors,
            "styles": request.preferred_styles,
            "gender": request.gender,
            "fit": request.fit_preference
        }

        logger.info(f"User preferences:\n{user_preferences} for the endpoint called /recommendations/complex")

        logger.info("Starting the recommendation generation")
        recommendations = await engine.get_recommendations(weather_conditions=weather_conditions,
                                                           user_preferences=user_preferences)
        logger.info(f"Recommendations:\n{recommendations} for the endpoint called /recommendations/complex")

        return recommendations

    except Exception as e:
        logger.error(f"Error in /recommendations/complex: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations.")



@router.post("/recommendations/simple", response_model=RecommendationResponse)
async def get_recommendations(location: str, engine: RecommendationEngine = Depends(get_recommendation_engine)) -> RecommendationResponse:
    """
    Generate outfit recommendations based on weather conditions.
    """
    logger.debug(f"Incoming request for location: {location}")

    try:
        # Fetch weather conditions from the Weather Service
        logger.info(msg="Obtaining the weather conditions for the endpoint called /recommendations/simple")
        weather_conditions = await engine.weather_client.get_weather(location)
        logger.info(f"Weather Conditions: {weather_conditions}")

        # Generate recommendations
        logger.info("Generation of the recommendations for the endpoint called /recommendations/simple")
        recommendations = await engine.get_simple_recommendations(weather_conditions=weather_conditions)
        logger.info(f"Recommendations output: {recommendations}")

        return recommendations

    except Exception as e:
        logger.info(f"Exception occur: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint triggered.")
    return {"status": "healthy"}
