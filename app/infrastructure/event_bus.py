from __future__ import annotations

"""
Implémentation infrastructure : bus d'événements local (sync).

Rôle
----
Implémenter `EventBusPort` (port domaine) sous forme d'un bus in-process, synchrone.

Objectifs
---------
- Permettre des side-effects post-commit (audit) en V1 sans broker externe.
- Ne jamais rollback la transaction principale si un handler échoue.

Intervient dans
--------------
- Composition root : `app/main.py` instancie `LocalEventBus` et enregistre des handlers.
- UoW : `app/adapters/persistence/unit_of_work.py` dispatch les events après commit.

Scénario nominal
----------------
- `register(event_type, handler)` : associe un handler à un type d'event.
- `publish(event)` : exécute les handlers enregistrés pour `type(event)`.

Cas alternatifs / exceptions
---------------------------
- Si aucun handler enregistré : no-op.
- Si un handler lève : log ERROR (structlog), mais continue (pas d'exception remontée).
"""

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
        """Enregistre un handler pour un type d'événement donné."""
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        """
        Publie un événement à tous les handlers enregistrés.

        Cas alternatifs
        - Si le handler échoue, log et continue.
        """
        log = get_logger()
        for handler in self._handlers.get(type(event), []):
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                log.error("event_handler_failed", event_type=type(event).__name__, error=str(exc))
