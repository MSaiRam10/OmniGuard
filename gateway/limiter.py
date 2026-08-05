import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True, protocol=2)

async def check_rate_limit(user_id: str, limit: int = 60, window: int = 60) -> bool:
    key = f"rate_limit:{user_id}"
    current_count = await redis_client.get(key)
    if current_count and int(current_count) >= limit:
        return False
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()
    return True

async def add_to_blocklist(user_id: str):
    await redis_client.set(f"blocklist:{user_id}", "blocked")

async def is_blocked(user_id: str) -> bool:
    result = await redis_client.get(f"blocklist:{user_id}")
    return result is not None
