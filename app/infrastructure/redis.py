from __future__ import annotations

"""
Infrastructure Redis (optionnel).

Rôle
----
Fournir les primitives Redis :
- construction d'un client async,
- healthcheck (PING),
- fermeture propre.

Objectifs
---------
- Encapsuler Redis hors des couches domaine/application.
- Permettre l'activation optionnelle via config (`REDIS_ENABLED`).

Intervient dans
--------------
- Composition root : `app/main.py` crée le client si activé et exécute `check_redis`.
- Readiness endpoint : `app/adapters/http/v1/health.py` lit `app.state.redis_ready`.
- Cache store : `app/adapters/cache/store.py` peut être construit depuis ce client.

Cas alternatifs / exceptions
---------------------------
- Redis down au boot : `check_redis` lève ; `app/main.py` capture et démarre en "degraded".
- `ping()` retourne une valeur inattendue : `RuntimeError`.

Workflows documentés
--------------------

Création client
~~~~~~~~~~~~~~~
Cas nominal
- `create_redis_client(REDIS_URL)` crée un client async (decode_responses=true).

Healthcheck Redis
~~~~~~~~~~~~~~~~~
Cas nominal
- `check_redis(client)` exécute `PING` et retourne si OK.

Cas d'exception
- Connexion/timeout/auth : lève une exception, capturée au niveau `lifespan` de l'app.
"""

from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    """Crée un client Redis async à partir d'une URL."""
    return Redis.from_url(redis_url, decode_responses=True)


async def check_redis(client: Redis) -> None:
    """Vérifie Redis via `PING`."""
    pong = await client.ping()
    if pong is not True:
        raise RuntimeError("Redis ping failed")


async def close_redis(client: Redis) -> None:
    """Ferme proprement la connexion Redis."""
    await client.aclose()
