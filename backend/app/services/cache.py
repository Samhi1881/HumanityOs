from abc import ABC, abstractmethod
from typing import Any
import redis.asyncio as redis
from app.core.config import settings

class CacheService(ABC):
    """Abstract Base Class for Cache Service interactions."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Retrieves a string value by key from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        """Sets a value by key in cache with optional expiration."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Deletes a key from cache."""
        pass


class RedisCacheService(CacheService):
    """Concrete implementation of CacheService using Redis."""

    def __init__(self) -> None:
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> str | None:
        """Retrieves value from Redis."""
        return await self.client.get(key)

    async def set(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        """Sets value in Redis."""
        await self.client.set(key, str(value), ex=expire_seconds)

    async def delete(self, key: str) -> None:
        """Deletes key from Redis."""
        await self.client.delete(key)
