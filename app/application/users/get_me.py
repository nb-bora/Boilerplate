from __future__ import annotations

from app.application.users.dto import UserOutput
from app.domain.users.exceptions import UserNotFound


class GetCurrentUser:
    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, user_id: str) -> UserOutput:
        async with self.uow:
            user = await self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFound()
            return UserOutput(
                id=user.id,
                email=user.email.value,
                roles=[r.value for r in user.roles],
                is_active=user.is_active,
            )
