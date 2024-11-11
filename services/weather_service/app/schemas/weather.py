from typing import Optional
from pydantic import BaseModel, Field, model_validator


class WeatherBase(BaseModel):
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


class WeatherResponse(WeatherBase):
    location: str = Field(..., description="Location Name")
    country: str = Field(..., description="Country Code")
    timestamp: int = Field(..., description="UNIX timestamp of the weather data")
    sunrise: int = Field(..., description="UNIX timestamp for sunrise")
    sunset: int = Field(..., description="UNIX timestamp for sunset")


class WeatherRequest(BaseModel):
    city: Optional[str] = Field(None, description="City name")
    country_code: Optional[str] = Field(None, description="ISO 3166 country code")
    latitude: Optional[float] = Field(None, description="Latitude for location")
    longitude: Optional[float] = Field(None, description="Longitude for location")

    @model_validator(mode="before")
    def check_location(self):
        """
        Validates in XOR that either:
        - city and optionally country_code are provided, OR
        - latitude and longitude are provided
        """
        if self.city:
            return self
        elif self.latitude is not None and self.longitude is not None:
            return self
        else:
            raise ValueError("Request need whether the city (with optional country code) or both lat and lon.")

    class Config:
        json_schema_extra = {
            "examples": [
                {"city": "Warsaw", "country_code": "PL"},
                {"latitude": 52.2297, "longitude": 21.0122}
            ]
        }
