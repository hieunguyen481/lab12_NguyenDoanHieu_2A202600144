"""Redis-backed monthly budget guard."""
from datetime import datetime

from fastapi import HTTPException

from app.config import settings
from app.storage import redis_client

INPUT_PRICE_PER_1K = 0.00015
OUTPUT_PRICE_PER_1K = 0.0006


def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return round(
        (input_tokens / 1000) * INPUT_PRICE_PER_1K + (output_tokens / 1000) * OUTPUT_PRICE_PER_1K,
        6,
    )


def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int) -> dict:
    month_key = _current_month()
    key = f"budget:{user_id}:{month_key}"
    current = float(redis_client.get(key) or 0.0)
    estimated_cost = estimate_cost(input_tokens, output_tokens)
    total = current + estimated_cost
    if total > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Monthly budget exceeded. Current: ${current:.4f}, "
                f"estimated: ${estimated_cost:.4f}, limit: ${settings.monthly_budget_usd:.2f}"
            ),
        )
    redis_client.incrbyfloat(key, estimated_cost)
    redis_client.expire(key, 32 * 24 * 3600)
    return {
        "current_cost_usd": round(total, 6),
        "budget_remaining_usd": round(settings.monthly_budget_usd - total, 6),
    }
