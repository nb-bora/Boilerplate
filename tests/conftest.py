from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from fastapi import Request

from app.adapters.http.dependencies import get_uow
from app.domain.users.entity import User
from app.main import create_app


@pytest.fixture
async def app():
    app = create_app()
    async with LifespanManager(app):
        yield app


class _FakeUsersRepo:
    def __init__(self) -> None:
        self._users_by_email: dict[str, User] = {}
        self._users_by_id: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower().strip())

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    async def add(self, user: User) -> None:
        self._users_by_email[user.email.value] = user
        self._users_by_id[user.id] = user


class _FakeRefreshTokensRepo:
    async def add_active(self, *, user_id: str, jti: str, expires_days: int) -> None:  # noqa: ARG002
        return

    async def get_active(self, *, jti: str):  # noqa: ANN001, ARG002
        return object()

    async def revoke(self, *, jti: str) -> None:  # noqa: ARG002
        return


class _FakeAuditRepo:
    async def add(self, audit_log) -> None:  # noqa: ANN001, ARG002
        return


class _FakeUow:
    def __init__(self) -> None:
        self.users = _FakeUsersRepo()
        self.refresh_tokens = _FakeRefreshTokensRepo()
        self.audit_logs = _FakeAuditRepo()
        self._events: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        return

    def collect_event(self, event) -> None:  # noqa: ANN001
        self._events.append(event)

    async def commit(self) -> None:
        return


@pytest.fixture
async def contract_app(app):
    async def _override_get_uow(request: Request):  # noqa: ARG001
        return _FakeUow()

    app.dependency_overrides[get_uow] = _override_get_uow
    yield app
