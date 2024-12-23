from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.recommendations import RecommendationResponse
from app.schemas.weather import WeatherConditions
from app.services.recommendation_kernel.engine import RecommendationEngine
from app.dependencies import get_recommendation_engine


router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request model for recommendations"""
    location: str
    style_preferences: Optional[List[str]] = []
    gender: Optional[str] = "unisex"
    fit_preference: Optional[str] = "normal"


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations_complex(request: RecommendationRequest,
                              engine: RecommendationEngine = Depends(get_recommendation_engine)) -> RecommendationResponse:
    """Get outfit recommendations based on weather and user preferences."""
    print(f"Incoming request: {request}")
    weather_conditions = await engine.weather_client.get_weather(request.location)
    print(f"Weather Conditions: {weather_conditions}")

    user_preferences = {
        "style": request.style_preferences,
        "gender": request.gender,
        "fit": request.fit_preference
    }

    return await engine.get_recommendations(weather_conditions=weather_conditions, user_preferences=user_preferences)

@router.post("/recommendations/simple", response_model=RecommendationResponse)
async def get_recommendations(location: str, engine: RecommendationEngine = Depends(get_recommendation_engine)) -> RecommendationResponse:
    """
    Generate outfit recommendations based on weather conditions.
    """
    print(f"Incoming request for location: {location}")

    try:
        # Fetch weather conditions from the Weather Service
        weather_conditions = await engine.weather_client.get_weather(location)

        # Generate recommendations
        recommendations = await engine.get_simple_recommendations(weather_conditions=weather_conditions)
        return recommendations
    except Exception as e:
        print(f"Exception occur: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
