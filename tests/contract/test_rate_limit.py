from __future__ import annotations

"""
Tests de contrat : rate limiting.

Rôle
----
Valider qu'une limite dépassement renvoie :
- status HTTP 429,
- enveloppe d'erreur,
- code `TECH.RATE_LIMIT.TOO_MANY_REQUESTS`.

Intervient dans
--------------
- Route : `app/adapters/http/v1/auth.py::login`
- Rate limiter : `app/adapters/cache/rate_limiter.py`
- Exception mapping : `app/adapters/http/exception_handlers.py` (429 → TECH.RATE_LIMIT.*)

Scénarios nominaux / alternatifs
-------------------------------
- L'endpoint `/auth/login` peut renvoyer 200/401 pour la première requête (selon backend),
  mais la seconde doit renvoyer 429 une fois la limite atteinte.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_rate_limit_login_returns_429_envelope(contract_app):
    """
    Vérifie que dépasser la limite provoque un 429 enveloppé.

    Note
    - `raise_app_exceptions=False` est requis pour tester le contrat HTTP (sinon les exceptions serveur
      remontent dans Pytest).
    """
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
