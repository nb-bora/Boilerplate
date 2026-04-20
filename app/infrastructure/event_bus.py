from __future__ import annotations

from collections.abc import Callable

from app.core.logging import get_logger
from app.domain.base import DomainEvent
from app.domain.events.bus import EventBusPort

EventHandler = Callable[[DomainEvent], None]


class LocalEventBus(EventBusPort):
    """
    Bus synchrone, dispatch POST-COMMIT uniquement.

    Règles :
    - Les événements sont collectés pendant la transaction
    - Le dispatch se fait APRÈS le commit, jamais pendant
    - Si un handler lève une exception : log ERROR, pas de rollback transaction principale
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def register(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        log = get_logger()
        for handler in self._handlers.get(type(event), []):
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                log.error("event_handler_failed", event_type=type(event).__name__, error=str(exc))
