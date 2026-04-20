from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.http.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware.request_id import RequestIdMiddleware
from app.infrastructure.db import check_db, create_engine, create_session_factory
from app.infrastructure.redis import check_redis, close_redis, create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log = get_logger()

    app.state.db_ready = False
    app.state.redis_ready = False
    app.state.redis_enabled = settings.REDIS_ENABLED

    engine = create_engine(settings.DATABASE_URL)
    app.state.db_engine = engine
    app.state.db_session_factory = create_session_factory(engine)

    redis = None
    if settings.REDIS_ENABLED:
        redis = create_redis_client(settings.REDIS_URL)
        app.state.redis = redis

    try:
        try:
            await check_db(engine)
            app.state.db_ready = True
        except Exception as exc:  # noqa: BLE001
            log.warning("db_check_failed", error=str(exc))

        if settings.REDIS_ENABLED and redis is not None:
            try:
                await check_redis(redis)
                app.state.redis_ready = True
            except Exception as exc:  # noqa: BLE001
                log.warning("redis_check_failed", error=str(exc))

        yield
    finally:
        if redis is not None:
            await close_redis(redis)
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.APP_LOG_LEVEL)

    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)
    return app


app = create_app()

