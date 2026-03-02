"""API Gateway – FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.database import engine

from app.routers import analytics, calls, health, shops, webhooks

logger = logging.getLogger(__name__)

settings = get_settings()


# ------------------------------------------------------------------ lifespan
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle hook."""
    logger.info("API Gateway starting up")
    yield
    logger.info("API Gateway shutting down")
    engine.dispose()


# ------------------------------------------------------------------ app
app = FastAPI(
    title="Call Intelligence Platform – API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

# ------------------------------------------------------------------ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ routers
app.include_router(health.router)
app.include_router(calls.router)
app.include_router(shops.router)
app.include_router(analytics.router)
app.include_router(webhooks.router)


# --------------------------------------------------------- exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler so unhandled errors return structured JSON."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500},
    )
