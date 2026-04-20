from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from ulid import ULID


def new_ulid() -> str:
    return str(ULID())


@dataclass(slots=True)
class Entity:
    id: str = field(default_factory=new_ulid)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ValueObject(Protocol):
    """Marker interface pour ValueObjects (immutables, égalité par valeur)."""


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: str = field(default_factory=new_ulid)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
