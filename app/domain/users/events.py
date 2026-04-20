from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.base import DomainEvent


@dataclass(frozen=True, slots=True)
class UserRegistered(DomainEvent):
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UserLoggedIn(DomainEvent):
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
