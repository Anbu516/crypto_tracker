import redis.asyncio as redis
from .config import settings


async def get_redis():
    pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
    return redis.Redis(connection_pool=pool)


redis_client = redis.from_url(settings.redis_url, decode_responses=True)
