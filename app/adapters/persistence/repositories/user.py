from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.mappers.user import to_domain, to_model
from app.adapters.persistence.models.user import UserModel
from app.domain.users.entity import User
from app.domain.users.repository import IUserRepository


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return to_domain(model) if model is not None else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return to_domain(model) if model is not None else None

    async def add(self, user: User) -> None:
        self._session.add(to_model(user))
