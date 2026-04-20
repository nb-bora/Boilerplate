from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_rate_limit_login_returns_429_envelope(contract_app):
    # réduire fortement la limite pour le test
    transport = ASGITransport(app=contract_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        contract_app.state.settings.RATE_LIMIT_LOGIN_PER_MINUTE = 1
        r1 = await client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "bad"})
        r2 = await client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "bad"})
    assert r1.status_code in (200, 401)  # selon DB dispo (ici, plutôt 401 via DomainError)
    assert r2.status_code == 429
    body = r2.json()
    assert body["success"] is False
    assert body["errors"][0]["code"] == "TECH.RATE_LIMIT.TOO_MANY_REQUESTS"
