from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import time
from typing import Protocol

from redis.asyncio import Redis


class ICacheStore(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl: int) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def incr(self, key: str, ttl: int) -> int: ...


class RedisCacheStore(ICacheStore):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def incr(self, key: str, ttl: int) -> int:
        # incr + set TTL si clé nouvelle
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.ttl(key)
            new_value, current_ttl = await pipe.execute()
        if current_ttl == -1:
            await self._client.expire(key, ttl)
        return int(new_value)


@dataclass(slots=True)
class _Entry:
    value: str
    expires_at: float


class InMemoryCacheStore(ICacheStore):
    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    async def _purge_expired(self) -> None:
        now = time()
        expired = [k for k, v in self._data.items() if v.expires_at <= now]
        for k in expired:
            self._data.pop(k, None)

    async def get(self, key: str) -> str | None:
        async with self._lock:
            await self._purge_expired()
            entry = self._data.get(key)
            return entry.value if entry is not None else None

    async def set(self, key: str, value: str, ttl: int) -> None:
        async with self._lock:
            await self._purge_expired()
            self._data[key] = _Entry(value=value, expires_at=time() + ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)

    async def incr(self, key: str, ttl: int) -> int:
        async with self._lock:
            await self._purge_expired()
            entry = self._data.get(key)
            if entry is None:
                self._data[key] = _Entry(value="1", expires_at=time() + ttl)
                return 1
            try:
                n = int(entry.value) + 1
            except ValueError:
                n = 1
            entry.value = str(n)
            return n
