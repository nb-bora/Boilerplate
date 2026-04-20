from __future__ import annotations

"""
Briques de base du domaine : Entity, ValueObject, DomainEvent.

Rôle
----
- `Entity` : base d'entité avec `id` + timestamps.
- `ValueObject` : marker pour value objects (immutables, égalité par valeur).
- `DomainEvent` : structure d'événement de domaine émis par les use-cases.

Objectifs
---------
- Unifier les conventions d'identifiants (ULID string 26).
- Fournir un type commun pour le bus d'événements.

Intervient dans
--------------
- Entités : `app/domain/users/entity.py`, `app/domain/audit/entity.py`
- Events : `app/domain/users/events.py`
- Event bus : `app/domain/events/bus.py`
- UoW : `app/adapters/persistence/unit_of_work.py` bufferise et dispatch des `DomainEvent`.

Scénarios nominaux
-----------------
- Création d'une entité : `id` généré automatiquement si absent.
- Création d'un event : `event_id` et `occurred_at` générés automatiquement.

Cas alternatifs / exceptions
---------------------------
- ULID génération : ne devrait pas lever en usage normal.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from ulid import ULID


def new_ulid() -> str:
    """Génère un ULID (string 26)."""
    return str(ULID())


@dataclass(slots=True)
class Entity:
    """
    Base d'entité du domaine.

    Champs
    - `id` : ULID string 26.
    - `created_at` / `updated_at` : timestamps UTC.
    """

    id: str = field(default_factory=new_ulid)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ValueObject(Protocol):
    """Marker interface pour ValueObjects (immutables, égalité par valeur)."""


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """
    Evénement de domaine.

    Champs
    - `event_id` : ULID unique pour déduplication/traçage.
    - `occurred_at` : timestamp UTC.
    - `aggregate_id` : id de l'agrégat concerné (ex: user_id).
    - `payload` : données contextualisées (request_id/ip, attributs, etc.).
    """

    event_id: str = field(default_factory=new_ulid)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
