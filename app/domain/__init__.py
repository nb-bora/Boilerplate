from __future__ import annotations

"""
Package `app.domain`.

Rôle
----
Le domaine contient la logique métier pure (entités, value objects, événements, ports).
Il ne dépend pas de FastAPI, SQLAlchemy, Redis, ni d'aucun détail d'infrastructure.

Objectifs
---------
- Exprimer les invariants métier et les concepts (User, AuditLog, événements).
- Définir des *ports* (interfaces) que les adapters implémentent (repositories, event bus, clock).
- Produire des exceptions métier stables (`DOMAIN.*`).

Intervient dans
--------------
- Application : use-cases orchestrent le domaine.
- Adapters : persistence implémente les ports, HTTP mappe les exceptions vers des erreurs API.
"""
