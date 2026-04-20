from __future__ import annotations

"""
Entrée principale de l'application FastAPI.

Workflows documentés
--------------------

Lifespan (startup/shutdown)
~~~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Au démarrage, on charge la configuration via `Settings`.
- On crée l'engine SQLAlchemy async + un `session_factory`
  (1 session par requête, à implémenter ensuite).
- On crée le client Redis si `REDIS_ENABLED=true`.
- On exécute des checks de disponibilité (DB, Redis si activé) et on expose l'état via
  `app.state.*`.
- L'API devient disponible et les healthchecks reflètent l'état des dépendances.

Cas alternatifs
- Si Redis est désactivé, aucun client n'est créé et le readiness ne teste pas Redis.
- Si la DB ou Redis est indisponible au boot, l'app démarre quand même mais `/api/v1/health/ready`
  renverra `503` tant que les checks ne passent pas (stratégie "degraded but alive").

Cas d'exception
- Erreurs de connexion DB/Redis : capturées et loguées en WARNING afin d'éviter un crash
  au démarrage.
- Erreurs au shutdown : on tente toujours de fermer Redis et de disposer l'engine DB.

Remarque
--------
Cette version vise un "boilerplate runnable" : elle privilégie la robustesse DX (démarrage même si
les dépendances sont down) et l'observabilité (logs) plutôt qu'un fail-fast strict.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.cache.store import InMemoryCacheStore, RedisCacheStore
from app.adapters.http.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.adapters.http.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.security_headers import SecurityHeadersMiddleware
from app.domain.users.events import UserLoggedIn, UserRegistered
from app.infrastructure.audit_handler import make_audit_handler
from app.infrastructure.db import check_db, create_engine, create_session_factory
from app.infrastructure.event_bus import LocalEventBus
from app.infrastructure.redis import check_redis, close_redis, create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan FastAPI.

    Voir la doc module pour le détail des cas nominal/alternatifs/exceptions.
    """
    settings = get_settings()
    log = get_logger()

    app.state.settings = settings
    app.state.db_ready = False
    app.state.redis_ready = False
    app.state.redis_enabled = settings.REDIS_ENABLED
    app.state.app_env = settings.APP_ENV
    app.state.cache_store = InMemoryCacheStore()

    engine = create_engine(settings.DATABASE_URL)
    app.state.db_engine = engine
    app.state.db_session_factory = create_session_factory(engine)
    app.state.event_bus = LocalEventBus()
    # Audit post-commit : écrit dans audit_logs en tâche de fond.
    audit_handler = make_audit_handler(app.state.db_session_factory)
    app.state.event_bus.register(UserRegistered, audit_handler)
    app.state.event_bus.register(UserLoggedIn, audit_handler)

    redis = None
    if settings.REDIS_ENABLED:
        redis = create_redis_client(settings.REDIS_URL)
        app.state.redis = redis
        app.state.cache_store = RedisCacheStore(redis)

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
    """
    Crée l'instance FastAPI et enregistre middlewares/routers.

    Cas nominal
    - `RequestIdMiddleware` est ajouté en premier pour garantir les headers et la corrélation.
    - CORS est activé avec une liste d'origins issue de `CORS_ORIGINS`.
    - Le router V1 est inclus sous `/api/v1`.

    Cas d'exception
    - Si la config est invalide, `Settings()` peut lever une exception au chargement.
      (La validation avancée/stricte sera ajoutée au fur et à mesure.)
    """
    settings = get_settings()
    configure_logging(settings.APP_LOG_LEVEL)

    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Ordre des middlewares (README) :
    # 1) Security headers  2) Request ID  3) Logging  4) CORS
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(LoggingMiddleware)
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
