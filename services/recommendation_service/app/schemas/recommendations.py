from pydantic import BaseModel, Field
from typing import Optional, List
from pydantic import model_validator
from datetime import datetime


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
