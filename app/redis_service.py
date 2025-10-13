"""Minimal Redis helper with injected client."""

from typing import Any

from redis.client import Redis


class RedisService:
    """Convenience methods over a provided redis client."""

    def __init__(self, client: Redis) -> None:
        if client is None:
            raise ValueError("Redis client instance is required")
        self._client = client

    @property
    def client(self) -> Redis:
        return self._client


    def get_value(self, key: str) -> Any:
        return self._client.get(name=key)

    def lpop(self, queue: str) -> Any:
        return self._client.lpop(queue)
