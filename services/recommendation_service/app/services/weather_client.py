import aiohttp
import logging
from typing import Optional
from datetime import datetime

from ..core.exceptions import WeatherServiceException
from ..schemas.weather import WeatherData, WeatherConditions

logger = logging.getLogger(__name__)


class WeatherClient:
    """Client for interacting with the Weather Service."""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def get_weather(self, location: str, country_code: Optional[str] = None) -> WeatherConditions:
        """
        Get weather data for a specific location.

        Args:
            location: City name
            country_code: Optional ISO 3166 country code

        Returns:
            WeatherConditions object containing current weather data
        """
        try:
            endpoint = f"{self.base_url}/api/v1/weather"

            # Prepare request payload
            payload = {
                "city": location
            }
            if country_code:
                payload["country_code"] = country_code

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        endpoint,
                        json=payload,
                        timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        raise WeatherServiceException(
                            f"Weather service returned {response.status}: {error_detail}"
                        )

                    data = await response.json()

                    # Create WeatherData object
                    weather_data = WeatherData(
                        temperature=data["temperature"],
                        feels_like=data["feels_like"],
                        temperature_min=data.get("temperature_min"),
                        temperature_max=data.get("temperature_max"),
                        humidity=data["humidity"],
                        pressure=data["pressure"],
                        description=data["description"],
                        weather_group=data["weather_group"],
                        wind_speed=data["wind_speed"],
                        rain=data.get("rain", 0.0),
                        snow=data.get("snow", 0.0),
                        date=data.get("date"),
                        weather_id=data.get("weather_id"),
                        timestamp=datetime.fromtimestamp(data["timestamp"])
                    )

                    # Create and return WeatherConditions
                    return WeatherConditions(
                        temperature=weather_data.temperature,
                        description=weather_data,
                        wind_speed=weather_data.wind_speed,
                        rain=weather_data.rain,
                        snow=weather_data.snow,
                        location=data["location"],
                        timestamp=datetime.utcnow()
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to weather service: {str(e)}")
            raise WeatherServiceException(f"Failed to connect to weather service: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise WeatherServiceException(f"Failed to fetch weather data: {str(e)}")

    async def health_check(self) -> bool:
        """Check if the weather service is available."""
        try:
            endpoint = f"{self.base_url}/api/v1/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=self.timeout) as response:
                    if response.status == 200:
                        return True
                    logger.warning(f"Weather service health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Weather service health check failed: {str(e)}")
            return False
