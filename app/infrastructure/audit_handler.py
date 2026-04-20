from __future__ import annotations

"""
Handler d'audit (side-effect) branchable sur le bus d'événements.

Rôle
----
Créer un handler compatible `LocalEventBus` qui, pour chaque `DomainEvent`,
écrit un `AuditLog` en base *après commit* (car le UoW dispatch post-commit).

Objectifs
---------
- Ne pas impacter la transaction principale : l'écriture d'audit est faite en tâche de fond.
- Garantir que si l'audit échoue, l'opération métier reste validée.

Intervient dans
--------------
- Composition root : `app/main.py` crée le handler et l'enregistre sur `LocalEventBus`.
- Persistence : `SqlAlchemyAuditRepository` écrit le modèle `AuditLogModel`.

Scénario nominal
----------------
1) `make_audit_handler(session_factory)` retourne `handle(event)`.
2) `handle` planifie `_write()` via `asyncio.create_task`.
3) `_write` ouvre une session, ajoute un `AuditLog`, commit.

Cas alternatifs / exceptions
---------------------------
- DB down : la tâche échoue (exception dans task) ; l'opération principale reste OK.
- Payload sans request_id/ip : valeurs vides/None (best-effort).

Note
----
On conserve les tasks dans un `set` pour éviter une GC prématurée.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repositories.audit_log import SqlAlchemyAuditRepository
from app.domain.audit.entity import AuditLog
from app.domain.base import DomainEvent


def make_audit_handler(session_factory: async_sessionmaker[AsyncSession]):
    """
    Fabrique un handler d'audit.

    Paramètre
    - `session_factory` : factory SQLAlchemy pour ouvrir une session dédiée (hors transaction principale).
    """
    tasks: set[asyncio.Task] = set()

    def handle(event: DomainEvent) -> None:
        """Handler sync (compatible bus) qui planifie une écriture async."""
        async def _write() -> None:
            async with session_factory() as session:
                repo = SqlAlchemyAuditRepository(session)
                await repo.add(
                    AuditLog(
                        user_id=event.aggregate_id or None,
                        action=f"{type(event).__name__}",
                        resource="user",
                        resource_id=event.aggregate_id,
                        metadata=dict(event.payload or {}),
                        request_id=str((event.payload or {}).get("request_id") or ""),
                        ip_address=(event.payload or {}).get("ip"),
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                await session.commit()

        task = asyncio.create_task(_write())
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    return handle
