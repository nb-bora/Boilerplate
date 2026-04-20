from __future__ import annotations

"""
Événements de domaine (Users).

Rôle
----
Définir les événements émis par les use-cases Auth :
- `UserRegistered`
- `UserLoggedIn`

Objectifs
---------
- Permettre des side-effects post-commit (audit) sans impacter la transaction principale.

Intervient dans
--------------
- Use-cases : `app/application/auth/register.py`, `app/application/auth/login.py`
- Event bus : `app/infrastructure/event_bus.py`
- Handler audit : `app/infrastructure/audit_handler.py`
"""

from dataclasses import dataclass, field
from typing import Any

from app.domain.base import DomainEvent


@dataclass(frozen=True, slots=True)
class UserRegistered(DomainEvent):
    """Émis après inscription (post-commit)."""
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UserLoggedIn(DomainEvent):
    """Émis après login (post-commit)."""
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
