from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .core.exceptions import (OpenWeatherAPIException,
                              WeatherDataNotFoundException)
from typing import AsyncGenerator, AsyncContextManager
import logging
from app.api.v1 import routes
from app.config import get_settings
from app.dependencies import get_redis, get_weather_service
from app.services.cache_service import WeatherCacheService


settings = get_settings()
logger = logging.getLogger(__name__)


async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Weather Service")
    try:
        redis = await get_redis()
        weather_service = await get_weather_service()
        cache_service = WeatherCacheService(redis, weather_service)
        app.state.cache_service = cache_service
        await cache_service.start_background_task()
        yield  # Application is running
    except Exception as e:
        logger.error(f"Failed to init Weather Service: {str(e)}")
        raise
    finally:
        logger.info("Shutting down weather service")
        if hasattr(app.state, 'cache_service'):
            logger.info("Shutting Down Weather Service")
            await cache_service.stop_background_refresh()
            await redis.close()

app = FastAPI(
    title=settings.WEATHER_API_PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url=None,
    lifespan=app_lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # FYI before deployment to prod check the CORS (actual origins)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OpenWeatherAPIException)
async def openweather_api_exception_handler(request, exc):
    logger.error(f"OpenWeatherAPIException: {str(exc)}")
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Error communicating with the weather service."
        },
    )


@app.exception_handler(WeatherDataNotFoundException)
async def weather_data_not_found_exception_handler(request, exc):
    logger.warning(f"WeatherDataNotFoundException: {str(exc)}")
    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc)
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(reques, exc):
    logger.error(f"Validation Error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors()
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    print(f"str{exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error"
        },
    )


# routes
app.include_router(routes.router, prefix=settings.API_V1_STR)
