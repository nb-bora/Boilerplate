from __future__ import annotations

"""
Base ORM SQLAlchemy.

Rôle
----
Définir :
- la base Declarative (`Base`) et
- un `BaseModel` partagé (id ULID + timestamps).

Objectifs
---------
- Uniformiser les colonnes communes.
- Utiliser ULID (string 26) comme clé primaire par défaut (conforme README).

Intervient dans
--------------
- Models : `user.py`, `refresh_token.py`, `audit_log.py`
- Migrations : Alembic crée des colonnes compatibles.

Cas alternatifs / exceptions
---------------------------
- L'ID ULID est généré côté application ; si besoin, on peut aussi le générer côté DB.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from ulid import ULID


def _ulid_str() -> str:
    """Génère un ULID au format string (26 chars)."""
    return str(ULID())


class Base(DeclarativeBase):
    """Base declarative SQLAlchemy."""
    pass


class BaseModel(Base):
    """Mixin de colonnes communes (id + timestamps)."""
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=_ulid_str)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
