from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repositories.audit_log import SqlAlchemyAuditRepository
from app.adapters.persistence.repositories.refresh_token import SqlAlchemyRefreshTokenRepository
from app.adapters.persistence.repositories.user import SqlAlchemyUserRepository
from app.domain.base import DomainEvent
from app.infrastructure.event_bus import LocalEventBus


class AsyncUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], event_bus: LocalEventBus):
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._events: list[DomainEvent] = []
        self.session: AsyncSession | None = None

        self.users: SqlAlchemyUserRepository
        self.audit_logs: SqlAlchemyAuditRepository
        self.refresh_tokens: SqlAlchemyRefreshTokenRepository

    async def __aenter__(self) -> AsyncUnitOfWork:
        self.session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self.session)
        self.audit_logs = SqlAlchemyAuditRepository(self.session)
        self.refresh_tokens = SqlAlchemyRefreshTokenRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self.session is None:
            return
        try:
            if exc is not None:
                await self.session.rollback()
        finally:
            await self.session.close()

    def collect_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork not entered")
        await self.session.commit()
        self._dispatch_post_commit(self._events)
        self._events = []

    def _dispatch_post_commit(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
