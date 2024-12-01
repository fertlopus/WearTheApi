import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.api.v1.routes import router
from app.config import get_settings
from app.dependencies import get_recommendation_engine, get_asset_retriever, get_cache_handler
from app.core.exceptions import (RecommendationServiceException, WeatherServiceException,
                              LLMException, AssetRetrievalException)

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events handler."""
    logger.info("Starting up Recommendation Service")
    try:
        settings = get_settings()
        # Initialize core services without dependency injection
        cache = await get_cache_handler(settings)
        asset_retriever = await get_asset_retriever(settings)
        engine = await get_recommendation_engine(settings)

        # Store in app state
        app.state.cache = cache
        app.state.engine = engine
        app.state.asset_retriever = asset_retriever

        # Initialize asset retriever
        await asset_retriever.initialize()

        logger.info("Recommendation Service initialization completed successfully")
        logger.info(f"API documentation available at: {settings.API_V1_STR}/docs")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize Recommendation Service: {str(e)}")
        raise
    finally:
        logger.info("Shutting down Recommendation Service")
        if hasattr(app.state, 'cache') and app.state.cache:
            await app.state.cache.close()


app = FastAPI(
    title=settings.RECOMMENDATION_API_PROJECT_NAME,
    description="Service for generating weather-appropriate outfit recommendations",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url=None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(WeatherServiceException)
async def weather_service_exception_handler(request: Request, exc: WeatherServiceException):
    logger.error(f"WeatherServiceException: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )


@app.exception_handler(LLMException)
async def llm_exception_handler(request: Request, exc: LLMException):
    logger.error(f"LLMException: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )


@app.exception_handler(AssetRetrievalException)
async def asset_retrieval_exception_handler(request: Request, exc: AssetRetrievalException):
    logger.error(f"AssetRetrievalException: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )


@app.exception_handler(RecommendationServiceException)
async def recommendation_exception_handler(request: Request, exc: RecommendationServiceException):
    logger.error(f"RecommendationServiceException: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


# Include routes
app.include_router(
    router,
    prefix=settings.API_V1_STR
)
