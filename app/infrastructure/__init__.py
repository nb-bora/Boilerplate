from __future__ import annotations

"""
Package `app.infrastructure`.

Rôle
----
Implémentations concrètes "production-like" des ports et services techniques :
- DB (SQLAlchemy engine/session),
- Redis (client/health),
- clock système,
- event bus local,
- handler d'audit (side-effect post-commit).

Objectifs
---------
- Isoler le code dépendant de libs externes (SQLAlchemy, redis, asyncio) hors du domaine.
- Offrir des composants réutilisables par la composition root (`app/main.py`).
"""
