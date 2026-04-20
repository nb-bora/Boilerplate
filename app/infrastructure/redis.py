from __future__ import annotations

"""
Infrastructure Redis (optionnel).

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
