from __future__ import annotations

"""
Entité domaine : AuditLog.

Rôle
----
Représenter un enregistrement d'audit (traçabilité) côté domaine.

Objectifs
---------
- Capturer une action (ex: user.registered, user.logged_in) avec contexte (request_id, ip, metadata).
- Permettre de persister l'audit via un port (`IAuditRepository`) sans dépendre de l'ORM.

Intervient dans
--------------
- Infrastructure/handler : `app/infrastructure/audit_handler.py` crée des `AuditLog`.
- Adapter persistence : `app/adapters/persistence/repositories/audit_log.py` persiste.

Cas alternatifs / exceptions
---------------------------
- Champs optionnels (`user_id`, `ip_address`) peuvent être None.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.base import Entity


@dataclass(slots=True)
class AuditLog(Entity):
    """Enregistrement d'audit."""

    user_id: str | None = None
    action: str = ""
    resource: str = ""
    resource_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    ip_address: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
