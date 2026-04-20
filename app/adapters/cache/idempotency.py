from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from fastapi import Request

from app.adapters.cache.store import ICacheStore


@dataclass(slots=True)
class StoredResponse:
    payload_hash: str
    status_code: int
    headers: dict[str, str]
    body: dict


def _hash_payload(*, body: bytes, content_type: str, authorization: str | None) -> str:
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
    body = await request.body()
    content_type = request.headers.get("Content-Type") or ""
    authorization = request.headers.get("Authorization")
    return _hash_payload(body=body, content_type=content_type, authorization=authorization)
