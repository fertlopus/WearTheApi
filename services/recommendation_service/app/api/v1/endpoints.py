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
async def get_recommendations(request: RecommendationRequest,
                              engine: RecommendationEngine = Depends(get_recommendation_engine)) -> RecommendationResponse:
    """Get outfit recommendations based on weather and user preferences."""
    weather_conditions = await engine.weather_client.get_weather(request.location)

    user_preferences = {
        "style": request.style_preferences,
        "gender": request.gender,
        "fit": request.fit_preference
    }

    return await engine.get_recommendations(weather_conditions=weather_conditions, user_preferences=user_preferences)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
