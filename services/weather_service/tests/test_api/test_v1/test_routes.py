import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from ....app.schemas.weather import WeatherResponse


def test_health_check(test_client: TestClient):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_get_weather_cached(test_client: TestClient, redis):
    test_weather = {
        "location": "Warsaw",
        "temperature": 20.5,
        "feels_like": 18.4,
        "humidity": 65,
        "pressure": 1013,
        "description": "clear sky",
        "wind_speed": 3.5,
        "timestamp": 1234567890
    }

    await redis.set(
        "weather:london",
        WeatherResponse(**test_weather).model_dump_json(),
        ex=1800
    )

    response = test_client.post(
        "/api/v1/weather",
        json={"city": "London"}
    )

    assert response.status_code == 200
    assert response.json() == test_weather


@pytest.mark.asyncio
async def test_get_weather_api_call(test_client: TestClient):
    test_weather = {
        "location": "Warsaw",
        "temperature": 20.5,
        "feels_like": 18.4,
        "humidity": 65,
        "pressure": 1013,
        "description": "clear sky",
        "wind_speed": 3.5,
        "timestamp": 1234567890
    }
    with patch('app.services.openweather.OpenWeatherService.get_current_weather', new_callable=AsyncMock) as mgw:
        mgw.return_value = WeatherResponse(**test_weather)

        response = test_client.post(
            "/api/v1/weather",
            json={"city": "Warsaw"}
        )

        assert response.status_code == 200
        assert response.json() == test_weather
        mgw.assert_called_once_with("Warsaw", None)

