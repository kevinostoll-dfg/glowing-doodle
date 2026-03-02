"""Call Handler service - manages inbound/outbound calls via Twilio."""

import logging

from fastapi import FastAPI

from app.call_router import router as call_router
from shared.config import get_settings
from shared.schemas.common import HealthResponse

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Call Handler Service",
    description="Handles inbound/outbound calls, Twilio webhooks, and call routing",
    version="0.1.0",
)

app.include_router(call_router, tags=["calls"])


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    db_status = "unknown"
    redis_status = "unknown"

    # Check database connectivity
    try:
        from shared.database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Check Redis connectivity
    try:
        import redis

        r = redis.from_url(settings.redis_url)
        r.ping()
        r.close()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        database=db_status,
        redis=redis_status,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
