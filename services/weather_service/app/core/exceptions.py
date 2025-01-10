from typing import Optional
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class WeatherServiceException(HTTPException):
    """Base exception"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, log: bool = False):
        super().__init__(status_code=status_code, detail=detail)
        if log:
            logger.error(f"{self.__class__.__name__}: {detail}")


class OpenWeatherAPIException(WeatherServiceException):
    """Raised when OpenWeather API fails"""
    def __init__(self, detail: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE, log: bool = False):
        super().__init__(status_code=status_code, detail=detail)
        if log:
            logger.error(f"{self.__class__.__name__}: {detail}")


class WeatherDataNotFoundException(WeatherServiceException):
    """Raised when weather data is not found/corrupted"""
    def __init__(self, location: str, latitude: Optional[float] = None, longitude: Optional[float] = None):
        detail = f"Weather data not found for location: {location}"
        if latitude and longitude:
            detail += f" (lat: {latitude}, lon: {longitude}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidWeatherRequestException(WeatherServiceException):
    """Raised when a weather request is invalid"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
