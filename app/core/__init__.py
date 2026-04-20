from __future__ import annotations

"""
Package `app.core`.

Rôle
----
Le "core" regroupe les composants transverses techniques (non métier) utilisés par l'application :
- configuration (Settings),
- logging structuré,
- sécurité (hashing + JWT),
- middlewares HTTP (request_id, logs de requête, security headers),
- contexte de requête (contextvars).

Objectifs
---------
- Offrir des primitives stables et réutilisables par adapters/application/infrastructure.
- Centraliser les conventions (headers, logs, règles de config).
"""
