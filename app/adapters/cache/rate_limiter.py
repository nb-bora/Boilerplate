from __future__ import annotations

"""
Rate limiting (adapter-level) basé sur `ICacheStore`.

Rôle
----
Appliquer des limites de fréquence au niveau HTTP (ex: login/register) en utilisant un store
clé/valeur (Redis ou in-memory).

Objectifs
---------
- Réduire les attaques par brute force / abus.
- Garder la logique métier (use-cases) indépendante de la notion de rate limiting.

Intervient dans
--------------
- Routes : `app/adapters/http/v1/auth.py`
- Store : `app/adapters/cache/store.py`

Scénario nominal
----------------
1) Calcule une clé `ratelimit:{route}:{ip}`.
2) `incr` avec TTL = fenêtre.
3) Si compteur > limite → lève `HTTPException(429)`.

Cas alternatifs
--------------
- Si `request.client` est absent (certains environnements), utilise "unknown".

Exceptions
----------
- `HTTPException(429)` si la limite est dépassée.
- Les erreurs du store (Redis down) remontent et peuvent être gérées par les handlers globaux.
"""

from fastapi import HTTPException, Request

from app.adapters.cache.store import ICacheStore


async def enforce_rate_limit(
    *,
    request: Request,
    store: ICacheStore,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """
    Fait respecter une limite par IP sur une clé logique.

    Paramètres
    - `key` : identifiant logique (ex: "auth.login").
    - `limit` : nombre max d'appels.
    - `window_seconds` : durée de la fenêtre.
    """
    client_ip = (request.client.host if request.client else "unknown").strip()
    full_key = f"ratelimit:{key}:{client_ip}"
    count = await store.incr(full_key, ttl=window_seconds)
    if count > limit:
        raise HTTPException(status_code=429, detail="Too many requests")
