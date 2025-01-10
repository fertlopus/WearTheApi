from typing import List, Optional
from pydantic import BaseModel, Field


class MainWeatherInfo(BaseModel):
    temperature: float = Field(..., alias="temp", description="Temperature in degrees Celsius")
    feels_like: float = Field(..., description="Feels like temperature in degrees Celsius")
    temperature_min: float = Field(..., alias="temp_min", description="Minimum temperature in degrees Celsius")
    temperature_max: float = Field(..., alias="temp_max", description="Maximum temperature in degrees Celsius")
    pressure: int = Field(..., description="Atmospheric pressure on the sea level, hPa")
    sea_level: int = Field(..., description="Atmospheric pressure on the sea level, hPa")
    ground_level: int = Field(..., alias="grnd_level", description="Atmospheric pressure on the ground level, hPa")
    humidity: int = Field(..., description="Humidity level in %")
    temp_kf: float = Field(..., description="Internal parameter for forecast calculation")

    class Config:
        populate_by_name = True


class WeatherCondition(BaseModel):
    id: int = Field(..., description="Weather condition id")
    main: str = Field(..., description="Group of weather parameters (Rain, Snow, Clouds etc.)")
    description: str = Field(..., description="Weather condition within the group")
    icon: str = Field(..., description="Weather icon id")


class CloudInfo(BaseModel):
    all: int = Field(..., description="Cloudiness percentage")


class WindInfo(BaseModel):
    speed: float = Field(..., description="Wind speed in meter/sec")
    deg: int = Field(..., description="Wind direction in degrees")
    gust: Optional[float] = Field(None, description="Wind gust speed in meter/sec")


class RainInfo(BaseModel):
    three_hour: Optional[float] = Field(None, alias="3h", description="Rain volume for last 3 hours, mm")

    class Config:
        populate_by_name = True


class SnowInfo(BaseModel):
    three_hour: Optional[float] = Field(None, alias="3h", description="Snow volume for last 3 hours, mm")

    class Config:
        populate_by_name = True


class SystemInfo(BaseModel):
    pod: str = Field(..., description="Part of the day (n - night, d - day)")


class ForecastPoint(BaseModel):
    dt: int = Field(..., description="Time of forecasted data, unix UTC")
    main: MainWeatherInfo
    weather: List[WeatherCondition]
    clouds: CloudInfo
    wind: WindInfo
    visibility: Optional[int] = Field(None, description="Average visibility in meters")
    pop: float = Field(..., description="Probability of precipitation")
    rain: Optional[RainInfo] = None
    snow: Optional[SnowInfo] = None
    sys: SystemInfo
    dt_txt: str = Field(..., description="Time of forecasted data, ISO format")


class Coordinates(BaseModel):
    lat: float = Field(..., description="City latitude")
    lon: float = Field(..., description="City longitude")


class CityInfo(BaseModel):
    id: int = Field(..., description="City ID")
    name: str = Field(..., description="City name")
    coord: Coordinates = Field(..., description="City coordinates")  # Changed to nested structure
    country: str = Field(..., description="Country code (GB, JP etc.)")
    population: int = Field(..., description="City population")
    timezone: int = Field(..., description="Shift in seconds from UTC")
    sunrise: int = Field(..., description="Sunrise time, Unix UTC")
    sunset: int = Field(..., description="Sunset time, Unix UTC")

    class Config:
        populate_by_name = True


class ForecastResponse(BaseModel):
    code: str = Field(..., alias="cod", description="Internal parameter")
    message: int = Field(..., description="Internal parameter")
    count: int = Field(..., alias="cnt", description="Number of timestamps returned")
    forecast_points: List[ForecastPoint] = Field(..., alias="list", description="List of forecast data points")
    city: CityInfo

    class Config:
        populate_by_name = True
