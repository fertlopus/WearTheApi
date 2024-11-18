from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
    date: int = Field(..., description="The date of the weather prediction")
    weather_id: int = Field(..., description="Weather ID for conditions, e.g. Cloudy, Rainy and etc.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WeatherConditions(BaseModel):
    """Weather conditions for asset filtering."""
    temperature: float = Field(..., description="Current temperature")
    description: WeatherData = Field(..., description="Weather condition")
    wind_speed: Optional[float] = Field(0.0, description="Wind speed")
    rain: Optional[float] = Field(0.0, description="Rain volume")
    snow: Optional[float] = Field(0.0, description="Snow volume")

    class Config:
        use_enum_values = True
