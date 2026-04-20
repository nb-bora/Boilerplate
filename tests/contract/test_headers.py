from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_request_id_headers_always_present(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/live")
    assert "X-Request-Id" in r.headers
    assert "X-Correlation-Id" in r.headers
