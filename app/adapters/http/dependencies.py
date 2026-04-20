from __future__ import annotations

"""
Dépendances FastAPI (couche Adapter HTTP).

Rôle
----
Ce module expose des *providers* FastAPI (via `Depends`) pour injecter, par requête HTTP :
- une session DB (SQLAlchemy AsyncSession) lorsque nécessaire,
- un `UnitOfWork` applicatif (transaction + repos + dispatch d'events post-commit),
- un cache store unifié (Redis si activé, sinon in-memory),
- l'identité de l'utilisateur courant (extrait du JWT Bearer).

Objectifs
---------
- Centraliser le wiring HTTP → infrastructure (app.state.*) sans fuiter ces détails dans les routes.
- Garantir un scope correct : 1 session DB par requête, et un UoW par use-case.
- Appliquer des règles transverses au niveau adapter HTTP (ex: blacklist `jti` si Redis activé).

Intervient dans
--------------
- Routes : `app/adapters/http/v1/auth.py`, `app/adapters/http/v1/users.py`
- Composition root (lifespan) : `app/main.py` initialise `app.state.db_session_factory`, `app.state.cache_store`,
  et le flag `app.state.redis_enabled`.
- Sécurité JWT : `app/core/security.py` (decode)
- Cache : `app/adapters/cache/store.py`
- Event bus : `app/infrastructure/event_bus.py` (si `app.state.event_bus` absent)

Scénarios nominaux
-----------------
- `get_db` : récupère `app.state.db_session_factory`, ouvre une session, la yield, puis ferme la session.
- `get_uow` : instancie un `AsyncUnitOfWork` avec `db_session_factory` + `event_bus`.
- `get_current_user_id` :
  - valide `Authorization: Bearer <token>`,
  - décode le JWT et extrait `sub` (user_id) et `jti`,
  - si Redis est activé, vérifie la blacklist `blacklist:jti:{jti}`,
  - expose `request.state.user_id` pour le logging.

Cas alternatifs
--------------
- `get_event_bus` : si aucun bus n'est attaché à `app.state`, en crée un et l'attache (fallback).
- `get_cache_store` : retourne toujours un store (Redis ou in-memory) car initialisé au startup.
- `get_current_user_id` : si Redis est désactivé, pas de vérification de blacklist.

Exceptions / erreurs attendues
------------------------------
- `get_db` / `get_uow` : si `app.state.db_session_factory` n'est pas initialisé (lifespan non exécuté),
  l'accès lèvera une `AttributeError` (erreur de câblage / tests sans lifespan).
- `get_current_user_id` :
  - `HTTPException(401)` si header absent/mal formé, ou token invalide/expiré, ou claims manquants.
  - `HTTPException(401)` si `jti` est blacklisted.
"""

from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.cache.store import ICacheStore
from app.adapters.persistence.unit_of_work import AsyncUnitOfWork
from app.core.security import decode_token
from app.infrastructure.event_bus import LocalEventBus


async def get_db(request: Request) -> AsyncSession:
    """
    Fournit une `AsyncSession` SQLAlchemy pour une requête HTTP.

    Rôle
    - Utilisé lorsque l'on veut injecter explicitement une session DB dans une route/adapter.

    Scénario nominal
    - Lit `request.app.state.db_session_factory` (créé dans `app/main.py` au startup).
    - Ouvre une session via `async with`.
    - Yield la session, puis la ferme automatiquement.

    Exceptions
    - `AttributeError` si `db_session_factory` n'existe pas (lifespan non démarré).
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.db_session_factory
    async with session_factory() as session:
        yield session


def get_event_bus(request: Request) -> LocalEventBus:
    """
    Retourne un bus d'événements local (synchrone) attaché à l'app.

    Scénario nominal
    - Retourne `request.app.state.event_bus` si présent.

    Cas alternatif
    - Si absent, instancie un `LocalEventBus` et l'attache à `app.state` (fallback).
    """
    bus = getattr(request.app.state, "event_bus", None)
    if bus is None:
        bus = LocalEventBus()
        request.app.state.event_bus = bus
    return bus


def get_cache_store(request: Request) -> ICacheStore:
    """
    Retourne le store de cache unifié (Redis ou in-memory).

    Interactions
    - Initialisé dans `app/main.py` au startup :
      - in-memory par défaut,
      - Redis si `REDIS_ENABLED=true`.
    """
    return request.app.state.cache_store


async def get_uow(request: Request) -> AsyncUnitOfWork:
    """
    Fournit un `AsyncUnitOfWork` prêt à l'emploi pour les use-cases.

    Scénario nominal
    - Récupère `db_session_factory` depuis `app.state`.
    - Récupère le bus via `get_event_bus`.
    - Retourne une instance `AsyncUnitOfWork(session_factory, event_bus)`.

    Note
    - Le UoW sera effectivement "ouvert" lors de `async with uow:` dans les use-cases.
    """
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.db_session_factory
    bus = get_event_bus(request)
    return AsyncUnitOfWork(session_factory=session_factory, event_bus=bus)


async def get_current_user_id(
    request: Request, authorization: str | None = Header(default=None, alias="Authorization")
) -> str:
    """
    Extrait et valide l'identité utilisateur depuis un JWT Bearer.

    Rôle
    - Dépendance des endpoints protégés (ex: `GET /api/v1/users/me`, `POST /api/v1/auth/logout`).

    Scénario nominal
    - Attend `Authorization: Bearer <token>`.
    - Décode le token via `app/core/security.py::decode_token`.
    - Extrait `sub` (user_id) et `jti`.
    - Si Redis activé, rejette si `blacklist:jti:{jti}` existe.
    - Stocke `request.state.user_id` (pour logs middleware) et retourne `user_id`.

    Cas alternatifs
    - Redis désactivé : pas de check blacklist.

    Exceptions (HTTP)
    - 401 si header absent/mauvais format, token invalide/expiré, claims manquants, ou token blacklisted.
    """
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
