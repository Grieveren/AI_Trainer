"""Redis connection with async support."""

import os
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self._client: Optional[Redis] = None
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._client is None:
            self._client = await redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
    ) -> None:
        """Set key-value pair with optional expiration (seconds)."""
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        """Delete key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> None:
        """Set key expiration."""
        await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        return await self.client.ttl(key)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> Redis:
    """Dependency to get Redis client."""
    if redis_client._client is None:
        await redis_client.connect()
    return redis_client.client
