from __future__ import annotations

"""
Unit of Work (persistance) — SQLAlchemy async + dispatch d'événements post-commit.

Rôle
----
Encapsuler une transaction applicative :
- ouvrir/fermer une session SQLAlchemy par use-case,
- exposer des repositories (users, refresh_tokens, audit_logs),
- collecter des DomainEvents pendant la transaction,
- dispatcher ces événements uniquement APRÈS commit (post-commit).

Objectifs
---------
- Une transaction par commande/use-case.
- Pas d'effets de bord (events) dans la transaction principale.

Intervient dans
--------------
- Use-cases : `app/application/auth/*.py`, `app/application/users/get_me.py`
- Repos : `app/adapters/persistence/repositories/*`
- Event bus : `app/infrastructure/event_bus.py`

Scénario nominal
----------------
1) `async with uow:` ouvre la session et instancie les repos.
2) Le use-case effectue ses opérations.
3) `uow.collect_event(...)` accumule les DomainEvents.
4) `await uow.commit()` :
   - commit DB,
   - dispatch des events via `LocalEventBus.publish`.
5) `__aexit__` ferme la session ; rollback automatique si exception dans le bloc.

Cas alternatifs / exceptions
---------------------------
- Si `commit()` appelé hors contexte (`__aenter__` non exécuté) : `RuntimeError`.
- Si exception dans le bloc `async with` : rollback best-effort.
- Les handlers d'events ne doivent pas casser la transaction (le bus log mais n'exceptionne pas).
"""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.persistence.repositories.audit_log import SqlAlchemyAuditRepository
from app.adapters.persistence.repositories.refresh_token import SqlAlchemyRefreshTokenRepository
from app.adapters.persistence.repositories.user import SqlAlchemyUserRepository
from app.domain.base import DomainEvent
from app.infrastructure.event_bus import LocalEventBus


class AsyncUnitOfWork:
    """Implémentation UoW pour SQLAlchemy AsyncSession."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], event_bus: LocalEventBus):
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._events: list[DomainEvent] = []
        self.session: AsyncSession | None = None

        self.users: SqlAlchemyUserRepository
        self.audit_logs: SqlAlchemyAuditRepository
        self.refresh_tokens: SqlAlchemyRefreshTokenRepository

    async def __aenter__(self) -> AsyncUnitOfWork:
        """
        Ouvre le scope transactionnel.

        Effets
        - Crée une `AsyncSession` via factory.
        - Instancie les repositories avec cette session.
        """
        self.session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self.session)
        self.audit_logs = SqlAlchemyAuditRepository(self.session)
        self.refresh_tokens = SqlAlchemyRefreshTokenRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        """
        Ferme le scope transactionnel.

        Scénario nominal
        - Si `exc` est non-None : rollback.
        - Ferme ensuite la session.
        """
        if self.session is None:
            return
        try:
            if exc is not None:
                await self.session.rollback()
        finally:
            await self.session.close()

    def collect_event(self, event: DomainEvent) -> None:
        """
        Enregistre un DomainEvent à dispatcher post-commit.

        Note
        - Méthode synchrone : elle ne fait que bufferiser en mémoire.
        """
        self._events.append(event)

    async def commit(self) -> None:
        """
        Commit DB + dispatch d'événements post-commit.

        Exceptions
        - `RuntimeError` si la session n'est pas initialisée (UoW non entré).
        """
        if self.session is None:
            raise RuntimeError("UnitOfWork not entered")
        await self.session.commit()
        self._dispatch_post_commit(self._events)
        self._events = []

    def _dispatch_post_commit(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
