from __future__ import annotations

"""
Configuration Alembic (mode async).

Workflows documentés
--------------------

Migration online (async)
~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- `DATABASE_URL` est lue via `Settings`.
- Alembic ouvre une connexion async et exécute les migrations.

Cas alternatifs
- Si `DATABASE_URL` n'est pas défini, on utilise la valeur par défaut de `Settings`.

Cas d'exception
- DB down / credentials invalides : Alembic échoue avec une erreur de connexion.

Notes
-----
Ce boilerplate V1 ne déclare pas encore de `Base.metadata` central (SQLAlchemy ORM complet).
Les migrations initiales utilisent donc des opérations Alembic/SQL explicites.
"""

from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import get_settings

# Alembic Config object, provides access to the values within the .ini file.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def get_url() -> str:
    return get_settings().DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        pool_pre_ping=True,
    )

    def do_run_migrations(sync_connection) -> None:  # noqa: ANN001
        context.configure(connection=sync_connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        import asyncio

        asyncio.run(run_migrations_online())


run_migrations()
