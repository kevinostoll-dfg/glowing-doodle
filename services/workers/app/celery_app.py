"""Celery application configuration for the workers service."""

from celery import Celery

from shared.config import get_settings

settings = get_settings()

celery = Celery(
    "call_intelligence_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    # Task routing: direct tasks to specialized queues
    task_routes={
        "app.tasks.transcription.*": {"queue": "transcription"},
        "app.tasks.analysis.*": {"queue": "analysis"},
        "app.tasks.notifications.*": {"queue": "notification"},
    },
    # Default retry policy
    task_default_retry_delay=60,
    task_annotations={
        "*": {
            "max_retries": 3,
            "retry_backoff": True,
        },
    },
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task discovery
    include=[
        "app.tasks.transcription",
        "app.tasks.analysis",
        "app.tasks.notifications",
    ],
)
