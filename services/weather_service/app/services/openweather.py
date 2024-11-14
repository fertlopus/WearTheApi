import random
import aiohttp
import asyncio
import logging
from typing import Dict, Optional

from app.core.exceptions import OpenWeatherAPIException, WeatherDataNotFoundException
from app.config import get_settings
from app.schemas.weather import WeatherResponse

logger = logging.getLogger(__name__)
settings = get_settings()

class OpenWeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_API_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session. Standard/Custom way."""
        try:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()
            return self.session
        except Exception as e:
            logging.error(f"Unable to open/close session for the service: {str(e)}")
            raise ValueError

    async def close(self):
        """Close the aiohttp session. Standard/Custom way"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception as e:
            logging.error(f"Unable to close session due to the error occured: {str(e)}")

    async def _make_request(self, endpoint: str, params: Dict[str, str]) -> Dict:
        """Make request to OpenWeather API with retry mechanism"""
        retries = settings.OPENWEATHER_API_RETRIES
        backoff_factor = settings.OPENWEATHER_BACKOFF_FACTOR

        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/{endpoint}",
                        params={"appid": self.api_key, **params},
                    ) as response:
                        if response.status == 404:
                            logger.error(f"Unknown location provided that caused the error: {params.get('q', '')}")
                            raise WeatherDataNotFoundException(params.get("q", "unknown location"))
                        response.raise_for_status()
                        data = await response.json()
                        # Data validation
                        if 'main' not in data or 'weather' not in data:
                            logger.error(f"Unsuccessful data validation, 'main' or 'weather' keys were not found.")
                            raise OpenWeatherAPIException("Incomplete data received from OpenWeather API call.")
                        return data
            except (aiohttp.ClientError, aiohttp.ClientResponseError,
                    aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                logger.error(f"Error in request processing from OpenWeather API: {str(e)}")
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}) for {endpoint} with params {params}: {str(e)}")
                if attempt == retries - 1:
                    raise OpenWeatherAPIException(f"Failed to fetch weather data after {retries} attempts.")
                await asyncio.sleep(backoff_factor * (2 ** attempt) + random.uniform(0, 0.1))

    async def get_current_weather(self, city: str, country_code: Optional[str] = None, units: str = "metric") -> WeatherResponse:
        """Get the current weather for a given city and optional country code."""
        location_query = f"{city},{country_code}" if country_code else city
        response = await self._make_request(
            "weather",
            {"q": location_query, "units": units}
        )
        return self._parse_weather_response(response)

    async def get_current_weather_by_coordinates(self, lat: float, lon: float, units: str="metric") -> WeatherResponse:
        """Get the current weather for a given latitude and longitude.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            units (str): Metric components ("imperial" or "metric" values)

        Returns:
            WeatherResponse: The weather data encapsulated in a response object.
        """
        response = await self._make_request(
            "weather",
            {"lat": str(lat), "lon": str(lon), "units": units}
        )
        return self._parse_weather_response(response)

    def _parse_weather_response(self, response: Dict) -> WeatherResponse:
        """Parse the OpenWeather API response and convert it to a WeatherResponse object

        Args:
            response (Dict): The JSON response from the API

        Returns:
            WeatherResponse: The parsed weather data
        """
        # Extract optional fields with defaults
        rain = response.get("rain", {}).get("1h", 0.0)
        snow = response.get("snow", {}).get("1h", 0.0)
        temperature_min = response["main"].get("temp_min")
        temperature_max = response["main"].get("temp_max")

        return WeatherResponse(
            location=response.get("name", "Unknown location"),
            country=response["sys"]["country"],
            temperature=response["main"]["temp"],
            feels_like=response["main"]["feels_like"],
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            humidity=response["main"]["humidity"],
            pressure=response["main"]["pressure"],
            description=response["weather"][0]["description"],
            weather_group=response["weather"][0]["main"],
            wind_speed=response["wind"]["speed"],
            rain=rain,
            snow=snow,
            date=response["dt"],
            timestamp=response["dt"],
            sunrise=response["sys"]["sunrise"],
            sunset=response["sys"]["sunset"],
        )

# async def main():
#     async with OpenWeatherService() as weather_service:
#         weather = await weather_service.get_current_weather_by_coordinates(lat=52.2297, lon=21.0122)
#         pprint(weather)
#
# if __name__ == "__main__":
#     asyncio.run(main())