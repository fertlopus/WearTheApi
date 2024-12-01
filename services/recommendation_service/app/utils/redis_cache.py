from typing import Optional
import logging
from redis.asyncio import Redis


logger = logging.getLogger(__name__)

class AsyncRedisCache:
    def __init__(self, redis_client: Redis, prefix: str = "recommendation_service:"):
        self.redis = redis_client
        self.prefix = prefix

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            full_key = f"{self.prefix}{key}"
            value = await self.redis.get(full_key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            raise ValueError(f"Failed to get from cache: {str(e)}")

    async def set(self, key: str, value: str, expire: int = 3600) -> None:
        """Set value in cache with expiration."""
        try:
            full_key = f"{self.prefix}{key}"
            await self.redis.set(full_key, value, ex=expire)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            raise ValueError(f"Failed to set in cache: {str(e)}")

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        try:
            full_key = f"{self.prefix}{key}"
            await self.redis.delete(full_key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            raise ValueError(f"Failed to delete from cache: {str(e)}")

    async def close(self) -> None:
        """Close Redis connection."""
        if hasattr(self.redis, 'close'):
            await self.redis.close()
