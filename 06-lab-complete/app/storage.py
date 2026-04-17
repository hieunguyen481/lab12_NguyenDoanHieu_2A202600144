"""Redis-backed storage helpers."""
import json
from datetime import datetime

import redis

from app.config import settings


redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def ping_redis() -> bool:
    redis_client.ping()
    return True


def get_history(user_id: str) -> list[dict]:
    raw = redis_client.get(f"history:{user_id}")
    return json.loads(raw) if raw else []


def append_history(user_id: str, role: str, content: str) -> list[dict]:
    history = get_history(user_id)
    history.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )
    history = history[-20:]
    redis_client.setex(f"history:{user_id}", settings.history_ttl_seconds, json.dumps(history))
    return history
