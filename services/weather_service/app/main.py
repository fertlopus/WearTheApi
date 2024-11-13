from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .core.exceptions import (OpenWeatherAPIException,
                              WeatherDataNotFoundException)
from typing import AsyncGenerator
import logging
from api.v1 import routes
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Weather Service")
    yield
    logger.info("Shutting down Weather Service")

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
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error"
        },
    )


# routes
app.include_router(routes.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting up Weather Service")

@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Shutting down Weather Service")

