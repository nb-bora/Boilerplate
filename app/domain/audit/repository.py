from __future__ import annotations

from typing import Protocol

from app.domain.audit.entity import AuditLog


class IAuditRepository(Protocol):
    async def add(self, audit_log: AuditLog) -> None: ...
