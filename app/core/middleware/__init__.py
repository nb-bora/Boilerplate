from __future__ import annotations

"""
Package `app.core.middleware`.

Rôle
----
Middlewares Starlette/FastAPI appliqués globalement (ordre défini dans `app/main.py`) :
- security headers,
- request_id / correlation_id,
- logging de requête.

Objectifs
---------
- Appliquer des comportements transverses sans polluer les routes/use-cases.
"""
