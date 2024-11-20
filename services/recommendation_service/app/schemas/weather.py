from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import model_validator


class WeatherData(BaseModel):
    temperature: float = Field(..., description="Temperature in degrees Celsius")
    feels_like: float = Field(..., description="Feels like temperature in degrees Celsius")
    temperature_min: Optional[float] = Field(None, description="Minimum temperature in degrees Celsius")
    temperature_max: Optional[float] = Field(None, description="Maximum temperature in degrees Celsius")
    humidity: int = Field(..., description="Humidity level in %")
    pressure: int = Field(..., description="Atmospheric pressure on the sea level, hPa")
    description: str = Field(..., description="Weather condition within group. Cand be defined on user language")
    weather_group: str = Field(..., description="Group of weather parameters (Rain, Snow, Clouds etc.)")
    wind_speed: float = Field(..., description="Wind speed in meter/sec")
    rain: Optional[float] = Field(None, description="Rain volume aka precipitation mm/h per 1h")
    snow: Optional[float] = Field(None, description="Snow volume aka precipitation mm/h per 1 h")
    date: Optional[int] = Field(None, description="The date of the weather prediction")  # Made optional
    weather_id: Optional[int] = Field(None, description="Weather condition ID")  # Made optional
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WeatherConditions(BaseModel):
    """Weather conditions for asset filtering."""
    temperature: float = Field(..., description="Current temperature")
    description: WeatherData = Field(..., description="Weather condition")
    wind_speed: Optional[float] = Field(0.0, description="Wind speed")
    rain: Optional[float] = Field(0.0, description="Rain volume")
    snow: Optional[float] = Field(0.0, description="Snow volume")
    location: str = Field(..., description="Location name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of weather reading")

    @model_validator(mode='after')
    def validate_precipitation(self) -> 'WeatherConditions':
        """Validate that rain and snow are not present simultaneously"""
        if (self.rain or 0) > 0 and (self.snow or 0) > 0:
            raise ValueError(
                "Cannot have both rain and snow precipitation simultaneously"
            )
        return self

    class Config:
        use_enum_values = True
