from __future__ import annotations

"""
Package `app.adapters`.

Rôle
----
Les *adapters* relient le cœur (domain/application) au monde extérieur :
- HTTP (FastAPI routers, schemas, dependencies, exception mapping),
- Persistence (SQLAlchemy repositories, models, unit of work),
- Cache (Redis/in-memory store, idempotency, rate limiting).

Objectif
--------
Isoler les dépendances techniques et permettre de les remplacer sans impacter le domaine.
"""
