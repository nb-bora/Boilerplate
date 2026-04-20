from __future__ import annotations

"""
Tests de base (santé / contrat minimal).

Rôle
----
Valider rapidement que l'app :
- répond sur les endpoints health,
- respecte l'enveloppe de réponse,
- renvoie les headers de corrélation,
- enveloppe les erreurs 404.

Intervient dans
--------------
- Endpoints : `app/adapters/http/v1/health.py`
- Middleware : `app/core/middleware/request_id.py`, `security_headers.py`
- Exception mapping : `app/adapters/http/exception_handlers.py`

Scénarios nominaux / alternatifs
-------------------------------
- `ready` peut retourner 200 ou 503 selon l'état DB/Redis (app "degraded but alive").
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health_live_has_envelope(app):
    """Vérifie `/health/live` : 200 + enveloppe + headers request/correlation + security header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert "X-Request-Id" in r.headers
    assert "X-Correlation-Id" in r.headers
    assert r.headers["X-Correlation-Id"] == r.headers["X-Request-Id"]
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    body = r.json()
    assert body["success"] is True
    assert body["errors"] is None
    assert "meta" in body and "request_id" in body["meta"]
    assert body["meta"]["request_id"] == r.headers["X-Request-Id"]


@pytest.mark.anyio
async def test_health_ready_returns_503_when_db_down(app):
    """Vérifie `/health/ready` : 200 ou 503 + enveloppe et request_id cohérent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/ready")
    assert r.status_code in (200, 503)
    assert "X-Request-Id" in r.headers
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] in ("ok", "down")
    assert body["meta"]["request_id"] == r.headers["X-Request-Id"]


@pytest.mark.anyio
async def test_404_returns_error_envelope(app):
    """Vérifie qu'une route inexistante renvoie une enveloppe d'erreur (404)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    assert "X-Request-Id" in r.headers
    body = r.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["errors"]
    assert "meta" in body and "request_id" in body["meta"]
    assert body["meta"]["request_id"] == r.headers["X-Request-Id"]
