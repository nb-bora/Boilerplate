from __future__ import annotations

"""
Tests de contrat : headers.

Rôle
----
Vérifier les en-têtes de corrélation exigés par le README :
- `X-Request-Id` toujours présent en réponse
- `X-Correlation-Id` toujours présent en réponse

Intervient dans
--------------
- Middleware : `app/core/middleware/request_id.py`
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_request_id_headers_always_present(app):
    """Toute réponse doit contenir les headers `X-Request-Id` et `X-Correlation-Id`."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/live")
    assert "X-Request-Id" in r.headers
    assert "X-Correlation-Id" in r.headers
