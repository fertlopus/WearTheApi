from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from pydantic.v1 import root_validator


class TemperatureRange(BaseModel):
    """TemperatureRange generic struct"""
    temperature_min: float = Field(..., alias="Min", description="Minimum temperature for temp range")
    temperature_max: float = Field(..., alias="Max", description="Maximum temperature for temp range")

    class Config:
        allow_population_by_field_name = True


class AssetItem(BaseModel):
    """Asset Item schema."""
    asset_name: str = Field(..., alias="AssetName", description="Name of the asset pointing to the file name")
    outfit_part: str = Field(..., alias="OutfitPart", description="Part of the outfit: head, footwear, bottom, top")
    color: str = Field(..., alias="Color", description="Color tag description of the AssetName, e.g. red etc.")
    style: List[str] = Field(..., alias="Style", description="Style tag/tags description of the AssetName, e.g. casual")
    gender: Literal['male', 'female', 'unisex'] = Field(..., alias="Gender", description="Gender pointer for the clothes/assets")
    fit: List[str] = Field(..., alias="Fit", description="Outfit type fit for the asset, e.g. normal, casual etc.")
    season: List[str] = Field(..., alias="Season", description="Season type for the outfit asset, e.g. summer")
    condition: List[str] = Field(..., alias="Condition", description="Weather condition for the outfit asset")
    temp_range: TemperatureRange = Field(..., alias="TempRange", description="Temperature range for the Weather")
    wind: str = Field(..., alias="Wind", description="Yes/No tag for wind suitability of the outfit")
    rain: str = Field(..., alias="Rain", description="Yes/No tag for rain suitability of the outfit")
    snow: str = Field(..., alias="Snow", description="Yes/No tag for snow suitability of the outfit")

    class Config:
        allow_population_by_field_name = True


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

    @root_validator
    def check_at_least_one_top_layer(cls, values):
        top, bottom = values.get("top"), values.get("bottom")
        if not top and not bottom:
            raise ValueError("At least one of 'top' or 'bottom' must be provided to build character.")
        return values


class RecommendationResponse(BaseModel):
    """Response containing multiple outfit recommendations"""
    recommendations: List[OutfitRecommendation]
    weather_summary: str
    style_notes: str

