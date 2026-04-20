from __future__ import annotations

"""
Modèle ORM : `refresh_tokens`.

Rôle
----
Persister les refresh tokens (rotation) avec `jti`, `expires_at`, `revoked_at`.

Intervient dans
--------------
- Repo : `app/adapters/persistence/repositories/refresh_token.py`
- Route refresh : `app/adapters/http/v1/auth.py`
- Migration : `alembic/versions/0002_auth_audit.py`
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.models.base import BaseModel


class RefreshTokenModel(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(String(26), index=True, nullable=False)
    jti: Mapped[str] = mapped_column(String(26), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
