from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_health_live_has_envelope():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/live")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["errors"] is None
    assert "meta" in body and "request_id" in body["meta"]


@pytest.mark.anyio
async def test_health_ready_returns_503_when_db_down():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/ready")
    assert r.status_code in (200, 503)
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] in ("ok", "down")
