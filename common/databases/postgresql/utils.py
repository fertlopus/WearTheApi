from typing import AsyncGenerator
import aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from config import get_db_settings

settings = get_db_settings()

# SQLAlchemy Setup
engine = create_async_engine(
    str(settings.postgres_dsn).replace('postgresql://', "postgresql+asyncpg://"),
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Redis setup
redis = aioredis.from_url(
    str(settings.redis_dsn),
    encoding='utf-8',
    decode_responses=True
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_redis():
    """Dependency for getting Redis connection"""
    return redis
