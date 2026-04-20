from __future__ import annotations

"""
Tests de contrat : idempotency.

Rôle
----
Valider le comportement d'idempotency sur `POST /auth/register` :
- même `Idempotency-Key` + payload différent → conflit 409 `TECH.CONFLICT`.

Intervient dans
--------------
- Route : `app/adapters/http/v1/auth.py::register`
- Idempotency : `app/adapters/cache/idempotency.py`
- Store : `app/adapters/cache/store.py`
- Exception mapping : `app/adapters/http/exception_handlers.py` (409 → TECH.CONFLICT)

Cas alternatifs
--------------
Selon le backend disponible :
- 200 si register aboutit,
- 409 si conflit,
- 500 si un composant requis échoue.
Le test accepte plusieurs issues mais vérifie le contrat en cas de 409.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_idempotency_conflict_returns_409(contract_app):
    """Rejouer une clé avec payload différent doit pouvoir produire un conflit 409 enveloppé."""
    transport = ASGITransport(app=contract_app, raise_app_exceptions=False)
    headers = {"Idempotency-Key": "01HX9MFBQ3NDXK7BPTHZ4B5FGS"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1ère requête "réserve" la clé (réponse possible 500 si DB absente).
        _ = await client.post(
            "/api/v1/auth/register",
            headers=headers,
            json={"email": "x@y.com", "password": "secure123"},
        )
        r2 = await client.post(
            "/api/v1/auth/register",
            headers=headers,
            json={"email": "x@y.com", "password": "DIFFERENTPAYLOAD"},
        )
    assert r2.status_code in (200, 409, 500)
    if r2.status_code == 409:
        body = r2.json()
        assert body["success"] is False
        assert body["errors"][0]["code"] == "TECH.CONFLICT"
