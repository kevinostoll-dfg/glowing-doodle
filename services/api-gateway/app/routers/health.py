"""Health-check endpoints."""

import redis
from fastapi import APIRouter
from sqlalchemy import text

from shared.config import get_settings
from shared.database import SessionLocal
from shared.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Basic liveness probe."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
def readiness():
    """Readiness probe – verifies database and Redis connectivity."""
    settings = get_settings()

    db_status = "unknown"
    redis_status = "unknown"

    # --- database check ---
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        finally:
            db.close()
    except Exception:
        db_status = "unavailable"

    # --- redis check ---
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unavailable"

    overall = "ok" if db_status == "connected" and redis_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
    )
