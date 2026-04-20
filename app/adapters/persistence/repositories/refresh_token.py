from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.models.refresh_token import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_active(self, *, user_id: str, jti: str, expires_days: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        self._session.add(
            RefreshTokenModel(user_id=user_id, jti=jti, expires_at=expires_at, revoked_at=None)
        )

    async def get_active(self, *, jti: str) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.jti == jti, RefreshTokenModel.revoked_at.is_(None)
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, *, jti: str) -> None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        res = await self._session.execute(stmt)
        token = res.scalar_one_or_none()
        if token is not None:
            token.revoked_at = datetime.now(timezone.utc)
