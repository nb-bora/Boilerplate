from __future__ import annotations

"""
Store de cache unifié (Redis optionnel, fallback in-memory).

Rôle
----
Fournir une interface unique (`ICacheStore`) utilisée par :
- rate limiting (`app/adapters/cache/rate_limiter.py`)
- idempotency (`app/adapters/cache/idempotency.py`)
- blacklist JWT (via `app/adapters/http/dependencies.py` et `logout`).

Objectifs
---------
- Permettre d'activer Redis via configuration sans changer le code métier.
- Offrir un fallback in-memory utilisable en dev/test (non distribué, best-effort).

Intervient dans
--------------
- Composition root : `app/main.py` instancie `InMemoryCacheStore` par défaut, et `RedisCacheStore` si Redis activé.

Scénarios nominaux
-----------------
- Redis : opérations déléguées au client `redis.asyncio.Redis`.
- In-memory : dictionnaire + TTL gérés en mémoire, protégés par un `asyncio.Lock`.

Cas alternatifs & limitations
----------------------------
- In-memory :
  - Non partagé entre processus/instances : rate limit/idempotency non distribués.
  - Les TTL expirent via purge opportuniste lors des accès.

Exceptions
----------
- Redis : erreurs réseau/timeout/auth remontent depuis la lib Redis (gérées plus haut si nécessaire).
"""

import asyncio
from dataclasses import dataclass
from time import time
from typing import Protocol

from redis.asyncio import Redis


class ICacheStore(Protocol):
    """
    Port de cache minimal pour features transverses.

    Contrat
    - `get` : retourne la valeur str stockée, ou None.
    - `set` : stocke une valeur avec TTL.
    - `delete` : supprime une clé.
    - `incr` : incrémente un compteur et garantit un TTL (fenêtre rate limit).
    """
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl: int) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def incr(self, key: str, ttl: int) -> int: ...


class RedisCacheStore(ICacheStore):
    """
    Implémentation Redis du cache store.

    Scénario nominal
    - Utilise `SET ... EX` pour TTL.
    - `incr` : pipeline INCR + TTL, et applique EXPIRE si TTL absent.
    """
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
    """
    Implémentation in-memory du cache store.

    Scénario nominal
    - Stocke `{key: _Entry(value, expires_at)}`.
    - Purge des expirations faite avant chaque opération.

    Cas alternatifs
    - Si la valeur existante n'est pas un int lors de `incr`, repart à 1.
    """
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
