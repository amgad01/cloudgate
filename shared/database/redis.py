from __future__ import annotations

from typing import Any

from redis.asyncio import ConnectionPool, Redis

from shared.config import BaseConfig


class RedisManager:
    def __init__(self, config: BaseConfig) -> None:
        self.config = config
        self._pool: ConnectionPool[Any] | None = None
        self._client: Redis[Any] | None = None

    @property
    def pool(self) -> ConnectionPool[Any]:
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                self.config.redis_url,
                password=self.config.redis_password,
                max_connections=20,
                decode_responses=True,
            )
        return self._pool

    @property
    def client(self) -> Redis[Any]:
        if self._client is None:
            self._client = Redis(connection_pool=self.pool)
        return self._client

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, expire: int | None = None) -> bool:
        return bool(await self.client.set(key, value, ex=expire))

    async def delete(self, key: str) -> int:
        return await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0

    async def incr(self, key: str) -> int:
        return await self.client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        return await self.client.ttl(key)

    async def hset(self, name: str, key: str, value: str) -> int:
        return await self.client.hset(name, key, value)

    async def hget(self, name: str, key: str) -> str | None:
        return await self.client.hget(name, key)

    async def hgetall(self, name: str) -> dict[str, str]:
        return await self.client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        return await self.client.hdel(name, *keys)

    async def lpush(self, key: str, *values: str) -> int:
        return await self.client.lpush(key, *values)

    async def rpush(self, key: str, *values: str) -> int:
        return await self.client.rpush(key, *values)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        return await self.client.lrange(key, start, end)

    async def publish(self, channel: str, message: str) -> int:
        return await self.client.publish(channel, message)

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    async def health_check(self) -> dict[str, Any]:
        try:
            await self.client.ping()
            return {"status": "healthy", "redis": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}


# Module-level Redis manager
_redis_manager: RedisManager | None = None


def init_redis(config: BaseConfig) -> RedisManager:
    global _redis_manager
    _redis_manager = RedisManager(config)
    return _redis_manager


def get_redis() -> RedisManager:
    if _redis_manager is None:
        raise RuntimeError("Redis not initialized. Call init_redis first.")
    return _redis_manager
