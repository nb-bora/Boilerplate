from __future__ import annotations

from ulid import ULID

from app.application.auth.dto import RegisterInput, TokenOutput
from app.core.config import get_settings
from app.core.context import get_ip, get_request_id
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.domain.users.entity import User
from app.domain.users.events import UserRegistered
from app.domain.users.exceptions import UserAlreadyExists
from app.domain.users.value_objects import Email, HashedPassword


class RegisterUser:
    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, data: RegisterInput) -> TokenOutput:
        settings = get_settings()
        async with self.uow:
            existing = await self.uow.users.get_by_email(data.email)
            if existing is not None:
                raise UserAlreadyExists()

            user = User(
                email=Email(data.email),
                hashed_password=HashedPassword(hash_password(data.password)),
            )
            await self.uow.users.add(user)

            refresh_jti = str(ULID())
            access_jti = str(ULID())
            await self.uow.refresh_tokens.add_active(
                user_id=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            self.uow.collect_event(
                UserRegistered(
                    aggregate_id=user.id,
                    payload={
                        "email": user.email.value,
                        "request_id": get_request_id(),
                        "ip": get_ip(),
                    },
                )
            )
            await self.uow.commit()

        return TokenOutput(
            access_token=create_access_token(
                subject=user.id,
                jti=access_jti,
                expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
            refresh_token=create_refresh_token(
                subject=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
