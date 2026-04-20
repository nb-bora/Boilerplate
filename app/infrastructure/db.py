from __future__ import annotations

"""
Infrastructure base de données (SQLAlchemy async).

Workflows documentés
--------------------

Création engine/session
~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- `create_engine(DATABASE_URL)` crée un `AsyncEngine`.
- `create_session_factory(engine)` crée une factory de `AsyncSession`.

Cas d'exception
- URL invalide ou driver manquant : SQLAlchemy lèvera lors de l'initialisation ou du premier usage.

Healthcheck DB
~~~~~~~~~~~~~~
Cas nominal
- `check_db(engine)` exécute `SELECT 1` et ne retourne rien si OK.

Cas d'exception
- Erreurs réseau/auth/timeout : lève une exception, capturée au niveau `lifespan` de l'app.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    """Crée un `AsyncEngine` avec `pool_pre_ping` pour limiter les connexions mortes."""
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Crée une factory de sessions async (expire_on_commit=false pour DX)."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def check_db(engine: AsyncEngine) -> None:
    """Vérifie la disponibilité DB via `SELECT 1`."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def lifespan_dispose_engine(engine: AsyncEngine) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await engine.dispose()
