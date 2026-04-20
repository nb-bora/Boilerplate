from __future__ import annotations

"""
Endpoints de healthchecks V1.

Workflows documentés
--------------------

`GET /api/v1/health/live`
~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Retourne `200` si le process répond (pas de dépendances externes).

Cas d'exception
- Aucun : cet endpoint doit rester ultra-fiable.

`GET /api/v1/health/ready`
~~~~~~~~~~~~~~~~~~~~~~~~~
Cas nominal
- Retourne `200` si la DB est OK, et si Redis est OK lorsque `REDIS_ENABLED=true`.

Cas alternatifs
- Redis désactivé : seul le check DB est exigé.
- Dépendance down : retourne `503` mais l'app reste vivante (voir `/live`).

Cas d'exception
- Si `app.state.*` est incomplet (mauvais câblage), on retombe sur `down` (comportement safe).
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.adapters.http.response import success

router = APIRouter(prefix="/health")


@router.get("/live")
async def live(request: Request):
    return success(request, data={"status": "ok"})


@router.get("/ready")
async def ready(request: Request):
    app = request.app

    checks: dict[str, str] = {}
    ready_ok = True

    db_ok = getattr(app.state, "db_ready", False)
    checks["db"] = "ok" if db_ok else "down"
    ready_ok = ready_ok and db_ok

    redis_enabled = getattr(app.state, "redis_enabled", False)
    if redis_enabled:
        redis_ok = getattr(app.state, "redis_ready", False)
        checks["redis"] = "ok" if redis_ok else "down"
        ready_ok = ready_ok and redis_ok

    status = "ok" if ready_ok else "down"
    payload = success(request, data={"status": status, "checks": checks})
    return JSONResponse(content=payload, status_code=200 if ready_ok else 503)
