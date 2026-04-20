from __future__ import annotations

from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    return Redis.from_url(redis_url, decode_responses=True)


async def check_redis(client: Redis) -> None:
    pong = await client.ping()
    if pong is not True:
        raise RuntimeError("Redis ping failed")


async def close_redis(client: Redis) -> None:
    await client.aclose()

