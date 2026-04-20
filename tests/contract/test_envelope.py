from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health_live_envelope_contract(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/live")
    body = r.json()
    assert body["success"] is True
    assert body["errors"] is None
    assert body["meta"]["request_id"] == r.headers["X-Request-Id"]
