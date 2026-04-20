from __future__ import annotations

"""
Repository SQLAlchemy : Audit logs.

Rôle
----
Persister des enregistrements d'audit (`AuditLog`) en DB.

Objectifs
---------
- Fournir un point d'écriture pour l'observabilité/traçabilité (inscription, login, etc.).
- Garder la couche domaine indépendante des détails SQLAlchemy.

Intervient dans
--------------
- Handler d'audit : `app/infrastructure/audit_handler.py` (écrit via une session dédiée)
- UoW : disponible aussi dans les transactions applicatives.

Cas alternatifs / exceptions
---------------------------
- Le flush/commit réel est géré par la couche appelante (UoW ou handler) :
  ce repo se contente de `session.add(...)`.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.models.audit_log import AuditLogModel
from app.domain.audit.entity import AuditLog
from app.domain.audit.repository import IAuditRepository


class SqlAlchemyAuditRepository(IAuditRepository):
    """Implémentation SQLAlchemy du port `IAuditRepository`."""
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, audit_log: AuditLog) -> None:
        """Ajoute un audit log (persisté au commit)."""
        self._session.add(
            AuditLogModel(
                id=audit_log.id,
                user_id=audit_log.user_id,
                action=audit_log.action,
                resource=audit_log.resource,
                resource_id=audit_log.resource_id,
                metadata_=audit_log.metadata,
                request_id=audit_log.request_id,
                ip_address=audit_log.ip_address,
                timestamp=audit_log.timestamp,
            )
        )
