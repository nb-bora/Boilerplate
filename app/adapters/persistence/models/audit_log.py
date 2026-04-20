from __future__ import annotations

"""
Modèle ORM : `audit_logs`.

Rôle
----
Stocker des événements d'audit applicatifs (inscription, login, etc.) avec contexte
(request_id, ip, metadata).

Intervient dans
--------------
- Repo : `app/adapters/persistence/repositories/audit_log.py`
- Handler : `app/infrastructure/audit_handler.py`
- Migration : `alembic/versions/0002_auth_audit.py`

Notes importantes
-----------------
- Le nom d'attribut Python `metadata` est réservé par SQLAlchemy ; on utilise donc `metadata_`
  tout en conservant la colonne SQL `"metadata"`.
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.models.base import BaseModel


class AuditLogModel(BaseModel):
    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(26), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    request_id: Mapped[str] = mapped_column(String(26), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
