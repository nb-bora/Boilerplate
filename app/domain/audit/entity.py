from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.base import Entity


@dataclass(slots=True)
class AuditLog(Entity):
    user_id: str | None = None
    action: str = ""
    resource: str = ""
    resource_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    ip_address: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
