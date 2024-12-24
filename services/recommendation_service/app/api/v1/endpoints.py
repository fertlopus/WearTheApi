from http.client import HTTPException
from typing import Optional, List
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from app.schemas.recommendations import RecommendationResponse
from app.schemas.weather import WeatherConditions
from app.services.recommendation_kernel.engine import RecommendationEngine
from app.dependencies import get_recommendation_engine


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
        weather_conditions = await engine.weather_client.get_weather(request.location)
        print(f"Weather conditions:\n{weather_conditions} for the endpoint called /recommendations/complex")

        user_preferences = {
            "colors": request.preferred_colors,
            "styles": request.preferred_styles,
            "gender": request.gender,
            "fit": request.fit_preference
        }

        print(f"User preferences:\n{user_preferences} for the endpoint called /recommendations/complex")
        recommendations = await engine.get_recommendations(weather_conditions=weather_conditions,
                                                           user_preferences=user_preferences)
        print(f"Recommendations:\n{recommendations} for the endpoint called /recommendations/complex")
        return recommendations
    except Exception as e:
        print(f"Error in /recommendations/complex: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations.")



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
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
