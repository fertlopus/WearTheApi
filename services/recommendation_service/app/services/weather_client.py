import aiohttp
import logging
from typing import Optional
from datetime import datetime

from ..core.exceptions import WeatherServiceException
from ..schemas.weather import WeatherData, WeatherConditions

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)


class WeatherClient:
    """Client for interacting with the Weather Service."""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
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
            endpoint = f"{self.base_url}api/v1/weather/city/{location}"
            logger.info(f"Requesting the endpoint: {endpoint}")

            # query params if country_code is provided
            params = {}
            if country_code:
                params["country_code"] = country_code

            async with (aiohttp.ClientSession() as session):
                async with session.get(endpoint, params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_detail = await response.text()
                        raise WeatherServiceException(
                            f"Weather service returned {response.status}: {error_detail}"
                        )

                    data = await response.json()
                    logger.info(f"Weather service returned response: {data}")

                    # Create WeatherData object
                    weather_data = self._map_response_to_weather_data(data)

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
            logger.info(f"Accessing the endpoint called --> {endpoint}")

            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=self.timeout) as response:
                    if response.status == 200:
                        return True
                    logger.warning(f"Weather service health check failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Weather service health check failed: {str(e)}")
            return False

    def _map_response_to_weather_data(self, response_json: dict) -> WeatherData:
        """Map the raw JSON response with WeatherData Pydantic model."""
        return WeatherData(
                        temperature=response_json["temperature"],
                        feels_like=response_json["feels_like"],
                        temperature_min=response_json.get("temperature_min"),
                        temperature_max=response_json.get("temperature_max"),
                        humidity=response_json["humidity"],
                        pressure=response_json["pressure"],
                        description=response_json["description"],
                        weather_group=response_json["weather_group"],
                        wind_speed=response_json["wind_speed"],
                        rain=response_json.get("rain", 0.0),
                        snow=response_json.get("snow", 0.0),
                        date=response_json.get("date"),
                        weather_id=response_json.get("weather_id"),
                        timestamp=datetime.fromtimestamp(response_json["timestamp"])
                    )
