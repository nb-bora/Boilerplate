from __future__ import annotations

"""
Repository SQLAlchemy : Refresh tokens.

Rôle
----
Gérer la persistance des refresh tokens (rotation / révocation).

Objectifs
---------
- Supporter la rotation lors de `/auth/refresh`.
- Garder l'auth JWT stateless côté access token, tout en persistants les refresh tokens en DB.

Intervient dans
--------------
- Route refresh : `app/adapters/http/v1/auth.py::refresh`
- UoW : `app/adapters/persistence/unit_of_work.py`
- Modèle : `app/adapters/persistence/models/refresh_token.py`

Scénarios nominaux
-----------------
- `add_active` : ajoute un refresh token non révoqué avec `expires_at`.
- `get_active` : retourne un refresh token actif (revoked_at NULL).
- `revoke` : positionne `revoked_at` (soft revoke).

Cas alternatifs
--------------
- `revoke` : si le token n'existe pas, no-op.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.models.refresh_token import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository:
    """Implémentation SQLAlchemy pour les refresh tokens."""
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_active(self, *, user_id: str, jti: str, expires_days: int) -> None:
        """Ajoute un refresh token actif (revoked_at=NULL)."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        self._session.add(
            RefreshTokenModel(user_id=user_id, jti=jti, expires_at=expires_at, revoked_at=None)
        )

    async def get_active(self, *, jti: str) -> RefreshTokenModel | None:
        """Récupère un refresh token actif par `jti`, ou None."""
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.jti == jti, RefreshTokenModel.revoked_at.is_(None)
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, *, jti: str) -> None:
        """Révoque un refresh token en positionnant `revoked_at`."""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        res = await self._session.execute(stmt)
        token = res.scalar_one_or_none()
        if token is not None:
            token.revoked_at = datetime.now(timezone.utc)
