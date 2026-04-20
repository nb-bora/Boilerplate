from __future__ import annotations

"""
Idempotency (adapter-level) pour endpoints sensibles (ex: register).

Rôle
----
Permet de rejouer une requête `POST` de manière sûre quand le client fournit un `Idempotency-Key` :
- Si même clé + même payload : renvoyer la réponse stockée.
- Si même clé + payload différent : renvoyer un conflit (409).

Objectifs
---------
- Eviter les doubles créations lors de retries réseau.
- Standardiser le comportement sans mélanger la logique d'idempotency dans les use-cases.

Intervient dans
--------------
- Route : `app/adapters/http/v1/auth.py::register`
- Store : `app/adapters/cache/store.py`

Scénario nominal
----------------
- `idempotency_payload_hash` calcule un hash SHA-256 stable à partir de :
  - body brut,
  - `Content-Type`,
  - `Authorization` (si présent).
- `idempotency_lookup` lit `idempotency:{key}` et reconstruit la réponse stockée.
- `idempotency_store` écrit la réponse enveloppée + headers + status_code + payload_hash avec TTL.

Cas alternatifs / exceptions
---------------------------
- Si aucune entrée en store, `lookup` retourne None.
- Les erreurs store (Redis down) remontent (l'endpoint peut échouer ou être géré plus haut).
"""

import hashlib
import json
from dataclasses import dataclass

from fastapi import Request

from app.adapters.cache.store import ICacheStore


@dataclass(slots=True)
class StoredResponse:
    """Représentation sérialisable d'une réponse HTTP stockée pour l'idempotency."""
    payload_hash: str
    status_code: int
    headers: dict[str, str]
    body: dict


def _hash_payload(*, body: bytes, content_type: str, authorization: str | None) -> str:
    """Calcule un hash SHA-256 du payload (body + meta headers)."""
    h = hashlib.sha256()
    h.update(body)
    h.update(content_type.encode("utf-8"))
    if authorization:
        h.update(authorization.encode("utf-8"))
    return h.hexdigest()


async def idempotency_lookup(
    *,
    store: ICacheStore,
    key: str,
) -> StoredResponse | None:
    """
    Cherche une réponse préalablement stockée pour une clé d'idempotency.

    Retour
    - `StoredResponse` si trouvée, sinon `None`.
    """
    raw = await store.get(f"idempotency:{key}")
    if raw is None:
        return None
    data = json.loads(raw)
    return StoredResponse(
        payload_hash=str(data.get("payload_hash") or ""),
        status_code=int(data["status_code"]),
        headers=dict(data.get("headers") or {}),
        body=dict(data.get("body") or {}),
    )


async def idempotency_store(
    *,
    store: ICacheStore,
    key: str,
    ttl_seconds: int,
    payload_hash: str,
    response: StoredResponse,
) -> None:
    """
    Stocke une réponse pour une clé d'idempotency, avec TTL.

    Remarque
    - Le `payload_hash` est stocké afin de détecter les conflits (même key, payload différent).
    """
    await store.set(
        f"idempotency:{key}",
        json.dumps(
            {
                "payload_hash": payload_hash,
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.body,
            }
        ),
        ttl=ttl_seconds,
    )


async def idempotency_payload_hash(request: Request) -> str:
    """
    Calcule le hash idempotency d'une requête HTTP.

    Cas alternatif
    - Si `Content-Type` absent, il est traité comme string vide.
    """
    body = await request.body()
    content_type = request.headers.get("Content-Type") or ""
    authorization = request.headers.get("Authorization")
    return _hash_payload(body=body, content_type=content_type, authorization=authorization)
