from typing import List, Literal, Union
from pydantic import BaseModel, Field, model_validator
from .base import OutfitPart, Gender


class TemperatureRange(BaseModel):
    """TemperatureRange generic struct"""
    temperature_min: float = Field(..., alias="Min", description="Minimum temperature for temp range")
    temperature_max: float = Field(..., alias="Max", description="Maximum temperature for temp range")

    @model_validator(mode="after")
    def validate_temperature_range(cls, values):
        t_min, t_max = values.temperature_min, values.temperature_max
        if not t_min and not t_max:
            raise ValueError("At least one of 'temperature_min' or 'temperature_max' must be provided to build character.")
        return values

    class Config:
        populate_by_name = True


class AssetItem(BaseModel):
    """Asset Item schema."""
    asset_name: str = Field(..., alias="AssetName", description="Name of the asset pointing to the file name")
    outfit_part: OutfitPart = Field(..., alias="OutfitPart", description="Part of the outfit: head, footwear, bottom, top")
    color: str = Field(..., alias="Color", description="Color tag description of the AssetName, e.g. red etc.")
    style: List[str] = Field(..., alias="Style", description="Style tag/tags description of the AssetName, e.g. casual")
    gender: Gender = Field(..., alias="Gender", description="Gender pointer for the clothes/assets")
    fit: Union[List[str], str] = Field(..., alias="Fit", description="Fit type for the asset, e.g., normal, casual, etc.")
    season: List[str] = Field(..., alias="Season", description="Season type for the outfit asset, e.g. summer")
    condition: List[str] = Field(..., alias="Condition", description="Weather condition for the outfit asset")
    temp_range: TemperatureRange = Field(..., alias="TempRange", description="Temperature range for the Weather")
    wind: Literal["yes", "no"] = Field(..., alias="Wind", description="Yes/No tag for wind suitability of the outfit")
    rain: Literal["yes", "no"] = Field(..., alias="Rain", description="Yes/No tag for rain suitability of the outfit")
    snow: Literal["yes", "no"] = Field(..., alias="Snow", description="Yes/No tag for snow suitability of the outfit")

    @property
    def normalized_fit(self) -> List[str]:
        return self.fit if isinstance(self.fit, list) else [self.fit]

    class Config:
        populate_by_name = True
