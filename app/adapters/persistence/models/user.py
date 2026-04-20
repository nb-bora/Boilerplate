from __future__ import annotations

"""
Modèle ORM : `users`.

Rôle
----
Représenter la table `users` en SQLAlchemy ORM.

Objectifs
---------
- Stocker les données nécessaires à l'auth (email, hashed_password, rôles, statut actif).
- Fournir un support simple pour `IUserRepository`.

Intervient dans
--------------
- Repo : `app/adapters/persistence/repositories/user.py`
- Mapper : `app/adapters/persistence/mappers/user.py`
- Migration : `alembic/versions/0001_initial.py` + `0002_auth_audit.py`

Cas alternatifs / exceptions
---------------------------
- `roles` est stocké en JSONB (PostgreSQL) : nécessite Postgres (cible V1).
"""

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.models.base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
