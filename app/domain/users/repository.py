from __future__ import annotations

from typing import Protocol

from app.domain.users.entity import User


class IUserRepository(Protocol):
    async def get_by_id(self, user_id: str) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...
