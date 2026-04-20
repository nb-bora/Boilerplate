from __future__ import annotations

"""
Configuration Pytest (fixtures) pour la suite de tests.

Rôle
----
Centraliser les fixtures utilisées par plusieurs modules de tests :
- `app` : instance FastAPI avec lifespan démarré (init `app.state.*`).
- `contract_app` : variante de l'app pour tests de contrat où l'on *override* la dépendance `get_uow`
  afin d'éviter une dépendance à Postgres/Redis/Docker.

Objectifs
---------
- Assurer que le lifespan (startup/shutdown) tourne pendant les tests (sinon `app.state.settings`,
  `db_session_factory`, etc. ne sont pas initialisés).
- Permettre des tests de contrat stables, rapides et indépendants des services externes.

Intervient dans
--------------
- Tous les tests : `tests/test_health.py` + `tests/contract/*`
- L'app créée vient de `app/main.py::create_app`.
- Override de dépendances FastAPI : `app/adapters/http/dependencies.py::get_uow`.

Scénarios nominaux
-----------------
- `app` :
  - crée l'app,
  - entre dans `LifespanManager` (startup),
  - yield l'app, puis shutdown.
- `contract_app` :
  - part de `app`,
  - override `get_uow` pour retourner un UoW fake,
  - yield l'app configurée.

Cas alternatifs / exceptions
---------------------------
- Si l'override n'a pas une signature compatible FastAPI (ex: param non typé),
  FastAPI peut interpréter le param comme input et renvoyer 422.
- Si l'on oublie `raise_app_exceptions=False` côté `ASGITransport`, les exceptions serveur
  remonteront dans Pytest au lieu d'être transformées en réponse HTTP enveloppée.
"""

import pytest
from asgi_lifespan import LifespanManager
from fastapi import Request

from app.adapters.http.dependencies import get_uow
from app.domain.users.entity import User
from app.main import create_app


@pytest.fixture
async def app():
    """
    Fixture d'application FastAPI avec lifespan actif.

    Scénario nominal
    - Permet aux tests de lire `app.state.settings`, `app.state.cache_store`, etc.
    """
    app = create_app()
    async with LifespanManager(app):
        yield app


class _FakeUsersRepo:
    """
    Faux repository Users (in-memory) pour tests de contrat.

    Objectif
    - Eviter Postgres tout en permettant des workflows simples (création + lookup).
    """

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
    """Faux repo refresh tokens (no-op / always active)."""

    async def add_active(self, *, user_id: str, jti: str, expires_days: int) -> None:  # noqa: ARG002
        return

    async def get_active(self, *, jti: str):  # noqa: ANN001, ARG002
        return object()

    async def revoke(self, *, jti: str) -> None:  # noqa: ARG002
        return


class _FakeAuditRepo:
    """Faux repo audit (no-op)."""

    async def add(self, audit_log) -> None:  # noqa: ANN001, ARG002
        return


class _FakeUow:
    """
    Faux Unit of Work pour tests de contrat.

    Rôle
    - Fournir les attributs attendus par les use-cases (users, refresh_tokens, audit_logs),
      et des méthodes `collect_event` + `commit`.

    Limitation
    - Aucune transaction réelle, aucun dispatch d'event (suffisant pour tests de contrat HTTP).
    """

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
    """
    Variante de l'app pour tests de contrat (sans DB).

    Détail important
    - Le param `request` doit être typé `fastapi.Request` pour être traité comme dépendance, sinon 422.
    """

    async def _override_get_uow(request: Request):  # noqa: ARG001
        return _FakeUow()

    app.dependency_overrides[get_uow] = _override_get_uow
    yield app
