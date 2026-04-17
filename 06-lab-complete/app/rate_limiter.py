"""Redis-backed sliding window rate limiter."""
import time

from fastapi import HTTPException

from app.config import settings
from app.storage import redis_client


def check_rate_limit(user_id: str) -> dict:
    now = time.time()
    key = f"rate:{user_id}"
    redis_client.zremrangebyscore(key, 0, now - 60)
    current = redis_client.zcard(key)
    if current >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    redis_client.zadd(key, {str(now): now})
    redis_client.expire(key, 60)
    return {
        "limit": settings.rate_limit_per_minute,
        "remaining": settings.rate_limit_per_minute - current - 1,
    }
