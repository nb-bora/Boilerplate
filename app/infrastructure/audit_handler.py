from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repositories.audit_log import SqlAlchemyAuditRepository
from app.domain.audit.entity import AuditLog
from app.domain.base import DomainEvent


def make_audit_handler(session_factory: async_sessionmaker[AsyncSession]):
    tasks: set[asyncio.Task] = set()

    def handle(event: DomainEvent) -> None:
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
