"""Production AI Agent - Day 12 final project."""
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_and_record_cost
from app.rate_limiter import check_rate_limit
from app.storage import append_history, get_history, ping_redis, redis_client
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
IS_READY = False
REQUEST_COUNT = 0
ERROR_COUNT = 0


class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    timestamp: str
    history_length: int
    budget_remaining_usd: float
    requests_remaining: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    global IS_READY
    logger.info(
        json.dumps(
            {
                "event": "startup",
                "app": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
            }
        )
    )
    ping_redis()
    IS_READY = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    IS_READY = False
    try:
        redis_client.close()
    except Exception:
        logger.exception(json.dumps({"event": "redis_close_failed"}))
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global REQUEST_COUNT, ERROR_COUNT
    REQUEST_COUNT += 1
    started = time.time()
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "ms": round((time.time() - started) * 1000, 1),
                }
            )
        )
        return response
    except Exception:
        ERROR_COUNT += 1
        logger.exception(json.dumps({"event": "request_failed", "path": request.url.path}))
        raise


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "history": "GET /history/{user_id} (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }


@app.post("/ask", response_model=AskResponse)
async def ask_agent(body: AskRequest, request: Request, _api_key: str = Depends(verify_api_key)):
    history = get_history(body.user_id)
    rate_info = check_rate_limit(body.user_id)
    input_tokens = len(body.question.split()) * 2 + sum(len(item["content"].split()) for item in history)
    append_history(body.user_id, "user", body.question)

    answer = llm_ask(body.question)
    output_tokens = len(answer.split()) * 2
    budget_info = check_and_record_cost(body.user_id, input_tokens, output_tokens)
    updated_history = append_history(body.user_id, "assistant", answer)

    logger.info(
        json.dumps(
            {
                "event": "agent_call",
                "user_id": body.user_id,
                "q_len": len(body.question),
                "history_length": len(updated_history),
                "client": str(request.client.host) if request.client else "unknown",
            }
        )
    )

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        history_length=len(updated_history),
        budget_remaining_usd=budget_info["budget_remaining_usd"],
        requests_remaining=rate_info["remaining"],
    )


@app.get("/history/{user_id}")
def history(user_id: str, _api_key: str = Depends(verify_api_key)):
    return {"user_id": user_id, "messages": get_history(user_id)}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": REQUEST_COUNT,
        "checks": {"llm": "mock" if not settings.openai_api_key else "openai"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not IS_READY:
        raise HTTPException(503, "Not ready")
    try:
        ping_redis()
    except Exception as exc:
        raise HTTPException(503, f"Redis unavailable: {exc}") from exc
    return {"ready": True}


@app.get("/metrics")
def metrics(_api_key: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": REQUEST_COUNT,
        "error_count": ERROR_COUNT,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "monthly_budget_usd": settings.monthly_budget_usd,
    }


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_signal)
