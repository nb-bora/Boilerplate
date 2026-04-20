from __future__ import annotations

from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.cache.store import ICacheStore
from app.adapters.persistence.unit_of_work import AsyncUnitOfWork
from app.core.security import decode_token
from app.infrastructure.event_bus import LocalEventBus


async def get_db(request: Request) -> AsyncSession:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.db_session_factory
    async with session_factory() as session:
        yield session


def get_event_bus(request: Request) -> LocalEventBus:
    bus = getattr(request.app.state, "event_bus", None)
    if bus is None:
        bus = LocalEventBus()
        request.app.state.event_bus = bus
    return bus


def get_cache_store(request: Request) -> ICacheStore:
    return request.app.state.cache_store


async def get_uow(request: Request) -> AsyncUnitOfWork:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.db_session_factory
    bus = get_event_bus(request)
    return AsyncUnitOfWork(session_factory=session_factory, event_bus=bus)


async def get_current_user_id(
    request: Request, authorization: str | None = Header(default=None, alias="Authorization")
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token") from None

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=401, detail="Invalid token") from None
    if not isinstance(jti, str) or not jti:
        raise HTTPException(status_code=401, detail="Invalid token") from None

    # Blacklist access token si Redis activé.
    if getattr(request.app.state, "redis_enabled", False):
        store: ICacheStore = request.app.state.cache_store
        if await store.get(f"blacklist:jti:{jti}") is not None:
            raise HTTPException(status_code=401, detail="Invalid token") from None

    request.state.user_id = user_id
    return user_id
