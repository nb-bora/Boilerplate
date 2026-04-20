from __future__ import annotations

"""
Infrastructure base de données (SQLAlchemy async).

Rôle
----
Fournir les primitives d'infrastructure DB :
- création d'engine async,
- création de factory de sessions,
- healthcheck DB (SELECT 1),
- helper lifespan pour disposer l'engine.

Objectifs
---------
- Encapsuler SQLAlchemy async hors des layers domaine/application.
- Offrir des primitives robustes pour la composition root (`app/main.py`).

Intervient dans
--------------
- Composition root : `app/main.py` crée `engine` + `db_session_factory` et exécute `check_db`.
- Readiness endpoint : `app/adapters/http/v1/health.py` lit `app.state.db_ready`.

Cas alternatifs / exceptions
---------------------------
- DB down au boot : `check_db` lève ; `app/main.py` capture et démarre en "degraded".
- URL invalide/driver manquant : erreurs SQLAlchemy lors de l'init ou première connexion.

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
    """
    Context manager async utilitaire pour disposer un engine.

    Usage
    - Peut être utilisé dans un lifespan composable si besoin.
    """
    try:
        yield
    finally:
        await engine.dispose()
