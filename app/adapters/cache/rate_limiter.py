from __future__ import annotations

from fastapi import HTTPException, Request

from app.adapters.cache.store import ICacheStore


async def enforce_rate_limit(
    *,
    request: Request,
    store: ICacheStore,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    client_ip = (request.client.host if request.client else "unknown").strip()
    full_key = f"ratelimit:{key}:{client_ip}"
    count = await store.incr(full_key, ttl=window_seconds)
    if count > limit:
        raise HTTPException(status_code=429, detail="Too many requests")
