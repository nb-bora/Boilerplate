from __future__ import annotations

"""
Port `IAuditRepository`.

Rôle
----
Définir l'interface de persistance des audit logs pour le domaine/application.

Intervient dans
--------------
- Adapter persistence : `app/adapters/persistence/repositories/audit_log.py` implémente ce port.
"""

from typing import Protocol

from app.domain.audit.entity import AuditLog


class IAuditRepository(Protocol):
    """Port de persistance des `AuditLog`."""
    async def add(self, audit_log: AuditLog) -> None: ...
