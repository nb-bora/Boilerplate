from __future__ import annotations

"""
Repository SQLAlchemy : Users.

Rôle
----
Adapter concret du port `IUserRepository` (domain) vers SQLAlchemy async.

Objectifs
---------
- Isoler SQLAlchemy (models/queries) du domaine/application.
- Retourner des entités domain (`app/domain/users/entity.py::User`).

Intervient dans
--------------
- UoW : `app/adapters/persistence/unit_of_work.py`
- Use-cases : register/login/get_me
- Mapper : `app/adapters/persistence/mappers/user.py`
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.mappers.user import to_domain, to_model
from app.adapters.persistence.models.user import UserModel
from app.domain.users.entity import User
from app.domain.users.repository import IUserRepository


class SqlAlchemyUserRepository(IUserRepository):
    """Implémentation SQLAlchemy du port `IUserRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        """Retourne un user par id (ou None)."""
        model = await self._session.get(UserModel, user_id)
        return to_domain(model) if model is not None else None

    async def get_by_email(self, email: str) -> User | None:
        """Retourne un user par email normalisé (lower/strip), ou None."""
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return to_domain(model) if model is not None else None

    async def add(self, user: User) -> None:
        """Ajoute un user (persisté au commit)."""
        self._session.add(to_model(user))
