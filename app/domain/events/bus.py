from __future__ import annotations

from typing import Protocol

from app.domain.base import DomainEvent


class EventBusPort(Protocol):
    def publish(self, event: DomainEvent) -> None: ...
