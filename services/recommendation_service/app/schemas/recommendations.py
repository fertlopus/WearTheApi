from pydantic import BaseModel, Field
from typing import Optional, List
from pydantic import model_validator
from datetime import datetime
from .weather import WeatherData


class OutfitRecommendation(BaseModel):
    """Structure for a single outfit recommendation"""
    # Outfits pieces
    head: Optional[str] = Field(None, description="Asset name for the head piece of outfit")
    footwear: str = Field(..., description=" Asset name for the footwear piece of outfit")
    bottom: str = Field(..., description="Asset name for the bottom piece of outfit")
    top: Optional[str] = Field(None, description="Asset name for the top piece of outfit")

    # Additional fields
    description: str = Field(..., description="Stylist's description")
    weather_appropriate_score: float = Field(..., ge=0.0, le=1.0)
    style_score: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Recommendation creation timestamp")


    @model_validator(mode="after")
    def validate_essential_parts(cls, values):
        """Ensure all essential outfit parts are included"""
        if not values.bottom:
            raise ValueError("Outfit recommendation must include a bottom (e.g., pants, skirt).")
        if not values.footwear:
            raise ValueError("Outfit recommendation must include footwear.")
        return values


class RecommendationResponse(BaseModel):
    """Response containing multiple outfit recommendations"""
    location: Optional[str]
    recommendations: List[OutfitRecommendation] = Field(..., description="Recommendations")
    weather_summary: str = Field(..., description="Summary of the current weather conditions")
    style_notes: str = Field(..., description="Additional styling notes and suggestions")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_recommendations(cls, values) -> 'RecommendationResponse':
        if not 1 <= len(values.recommendations) <= 5:
            raise ValueError("Number of recommendations must be between 1 and 10")
        return values


class CustomRecommendationRequest(BaseModel):
    """Request model. for the custom weather-based recommendations"""
    weather_data: WeatherData
    gender: Optional[str] = Field("unisex", description="Preferred gender model for the outfits")
    preferred_styles: Optional[List[str]] = Field(None, description="Array of the preferred styles for the outfits")
    preferred_colors: Optional[List[str]] = Field(None, description="Array of preferred colors for the outfits")
    fit_preferences: Optional[str] = Field(None, description="Array of preferred fit of outfits")


class CategorizedOutfitRecommendation(BaseModel):
    """Categorized recommendations response model"""
    # Outfit parts
    head: List[str] = Field(..., description="Ranked head outfit items, best matches first")
    top: List[str] = Field(..., description="Ranked top outfit items, best matches first")
    bottom: List[str] = Field(..., description="Ranked bottom outfit items, best matches first")
    footwear: List[str] = Field(..., description="Ranked footwear outfit items, best matches first")

    # Additional fields
    description: str = Field(None, description="Overall style notes and guidance")
    additional_notes: Optional[str] = Field(None, description="Weather-specific suggestions to outfits")


class CategorizedRecommendationResponse(BaseModel):
    """Response model for categorized recommendations endpoint"""
    recommendations: CategorizedOutfitRecommendation
    weather_summary: str = Field(..., description="Summary of weather conditions")
    style_notes: str = Field(..., description="Additional styling notes and suggestions")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generated at")
