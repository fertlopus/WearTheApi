import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import router as api_router
from .config import Settings, get_settings
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Setup logging
    setup_logging()

    # Create FastAPI app
    app = FastAPI(
        title="WearThe Recommendation Service",
        description="Service for generating weather-appropriate outfit recommendations",
        version="1.0.0"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info("Initializing recommendation service...")
        try:
            # Initialize asset retriever
            asset_retriever = app.dependency_overrides.get(
                get_asset_retriever,
                get_asset_retriever
            )()
            await asset_retriever.initialize()
            logger.info("Asset retriever initialized successfully")

            # Initialize cache if configured
            cache_handler = app.dependency_overrides.get(
                get_cache_handler,
                get_cache_handler
            )()
            if cache_handler:
                await cache_handler.initialize()
                logger.info("Cache initialized successfully")

        except Exception as e:
            logger.error(f"Error during startup: {str(e)}")
            raise

    return app


app = create_application()