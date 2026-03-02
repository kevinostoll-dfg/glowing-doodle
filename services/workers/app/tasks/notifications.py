"""Notification tasks for alerts and digests."""

import logging

from app.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    name="app.tasks.notifications.notify_low_score",
    max_retries=3,
    default_retry_delay=30,
)
def notify_low_score(self, call_id: int, score: float) -> dict:
    """Send a low-score alert notification.

    This is a placeholder implementation that logs the alert.
    In production, this would send notifications via email, Slack,
    SMS, or push notification to shop managers.

    Args:
        call_id: The database ID of the call with a low score.
        score: The AI-generated call quality score.

    Returns:
        Dict with call_id and notification status.
    """
    logger.warning(
        "LOW SCORE ALERT: Call %d scored %.1f (below threshold). "
        "Notification would be sent to shop managers.",
        call_id,
        score,
    )

    # TODO: Implement actual notification delivery
    # - Look up shop managers for the call's shop
    # - Send email via SendGrid / SES
    # - Send Slack webhook notification
    # - Send push notification via Firebase

    return {
        "call_id": call_id,
        "score": score,
        "notification_type": "low_score_alert",
        "status": "logged",
    }


@celery.task(
    bind=True,
    name="app.tasks.notifications.send_daily_digest",
    max_retries=3,
    default_retry_delay=60,
)
def send_daily_digest(self, shop_id: int) -> dict:
    """Send a daily call performance digest for a shop.

    This is a placeholder implementation that logs the digest trigger.
    In production, this would aggregate daily metrics and send a
    summary report to shop managers.

    Args:
        shop_id: The database ID of the shop to generate a digest for.

    Returns:
        Dict with shop_id and digest status.
    """
    logger.info(
        "DAILY DIGEST: Triggered for shop %d. "
        "Digest would be compiled and sent to shop managers.",
        shop_id,
    )

    # TODO: Implement actual daily digest
    # - Query CallMetrics for the shop's daily stats
    # - Aggregate call scores, sentiment distribution, missed calls
    # - Generate a formatted HTML email summary
    # - Send via email to all shop managers/admins

    return {
        "shop_id": shop_id,
        "notification_type": "daily_digest",
        "status": "logged",
    }
