from __future__ import annotations

from ulid import ULID

from app.application.auth.dto import LoginInput, TokenOutput
from app.core.config import get_settings
from app.core.context import get_ip, get_request_id
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.domain.users.events import UserLoggedIn
from app.domain.users.exceptions import InvalidCredentials, UserInactive


class LoginUser:
    def __init__(self, *, uow) -> None:  # noqa: ANN001
        self.uow = uow

    async def execute(self, data: LoginInput) -> TokenOutput:
        settings = get_settings()
        async with self.uow:
            user = await self.uow.users.get_by_email(data.email)
            # Anti-énumération : même exception pour "unknown email" et "bad password".
            if user is None:
                raise InvalidCredentials()
            if not user.is_active:
                raise UserInactive()
            if not verify_password(data.password, user.hashed_password.value):
                raise InvalidCredentials()

            refresh_jti = str(ULID())
            access_jti = str(ULID())
            await self.uow.refresh_tokens.add_active(
                user_id=user.id, jti=refresh_jti, expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            self.uow.collect_event(
                UserLoggedIn(
                    aggregate_id=user.id, payload={"request_id": get_request_id(), "ip": get_ip()}
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
