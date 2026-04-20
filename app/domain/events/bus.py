from __future__ import annotations

"""
Port `EventBusPort`.

Rôle
----
Définir l'interface de publication d'événements de domaine.

Objectifs
---------
- Découpler le domaine/application de l'implémentation (local sync, queue, Kafka...).

Intervient dans
--------------
- Infrastructure : `app/infrastructure/event_bus.py` implémente un bus local.
- UoW : dispatch post-commit via cette interface.
"""

from typing import Protocol

from app.domain.base import DomainEvent


class EventBusPort(Protocol):
    """Port minimal d'un bus d'événements."""
    def publish(self, event: DomainEvent) -> None: ...
