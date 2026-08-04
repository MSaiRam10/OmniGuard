import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(REDIS_URL, decode_responses=True, protocol=2)

async def check_rate_limit(user_id: str, limit: int = 60, window: int = 60) -> bool:
    """
    Check if the user has exceeded the rate limit. Returns True if allowed, Flase if rate-limited."""
    key = f"rate_limit:{user_id}"
    current_count = await redis_client.get(key)
    if current_count and int(current_count) >= limit:
        return False
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()
    return True