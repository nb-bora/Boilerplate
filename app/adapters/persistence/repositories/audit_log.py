from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.models.audit_log import AuditLogModel
from app.domain.audit.entity import AuditLog
from app.domain.audit.repository import IAuditRepository


class SqlAlchemyAuditRepository(IAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, audit_log: AuditLog) -> None:
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
