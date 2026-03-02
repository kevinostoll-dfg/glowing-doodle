"""Analysis tasks for scoring and evaluating call transcripts."""

import logging

from app.celery_app import celery
from app.integrations.claude_client import score_call
from app.prompts.scoring_rubric import DEFAULT_RUBRIC
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.playbook import Playbook
from shared.models.shop import Shop

logger = logging.getLogger(__name__)

LOW_SCORE_THRESHOLD = 60


@celery.task(
    bind=True,
    name="app.tasks.analysis.analyze_call",
    max_retries=3,
    default_retry_delay=60,
)
def analyze_call(self, call_id: int) -> dict:
    """Analyze a call transcript using Claude AI.

    Loads the call transcript and the shop's active playbook rubric,
    builds a scoring prompt, and sends it to the Anthropic Claude API.
    Parses the JSON response and updates the Call record with scores,
    sentiment, intent, key points, and coaching notes.

    If the score is below the threshold, triggers a low-score notification.

    Args:
        call_id: The database ID of the call to analyze.

    Returns:
        Dict with call_id, analysis_status, and ai_score.
    """
    logger.info("Starting analysis for call %d", call_id)

    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            logger.error("Call %d not found", call_id)
            return {"call_id": call_id, "analysis_status": "failed", "error": "Call not found"}

        if not call.transcript:
            logger.error("Call %d has no transcript", call_id)
            call.analysis_status = "failed"
            db.commit()
            return {"call_id": call_id, "analysis_status": "failed", "error": "No transcript"}

        # Mark as processing
        call.analysis_status = "processing"
        db.commit()

        # Load the shop name for context
        shop = db.query(Shop).filter(Shop.id == call.shop_id).first()
        shop_name = shop.name if shop else "Unknown Shop"

        # Load active playbook criteria, fall back to default rubric
        rubric_criteria = _load_rubric(db)

        # Call Claude API for scoring
        analysis_result = score_call(
            transcript=call.transcript,
            rubric_criteria=rubric_criteria,
            shop_name=shop_name,
        )

        # Update the Call record with analysis results
        call.ai_score = analysis_result["overall_score"]
        call.sentiment = analysis_result["sentiment"]
        call.caller_intent = analysis_result["intent"]
        call.key_points = analysis_result["key_points"]
        call.coaching_notes = analysis_result["coaching_notes"]
        call.analysis_status = "completed"

        db.commit()

        logger.info(
            "Analysis completed for call %d: score=%.1f, sentiment=%s, intent=%s",
            call_id,
            call.ai_score,
            call.sentiment,
            call.caller_intent,
        )

        # Trigger low-score notification if needed
        if call.ai_score < LOW_SCORE_THRESHOLD:
            from app.tasks.notifications import notify_low_score

            notify_low_score.delay(call_id, call.ai_score)

        return {
            "call_id": call_id,
            "analysis_status": "completed",
            "ai_score": call.ai_score,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Analysis failed for call %d: %s", call_id, exc)

        # Update status to failed
        try:
            call = db.query(Call).filter(Call.id == call_id).first()
            if call:
                call.analysis_status = "failed"
                db.commit()
        except Exception:
            logger.exception("Failed to update analysis_status for call %d", call_id)

        # Retry with exponential backoff
        raise self.retry(exc=exc)

    finally:
        db.close()


def _load_rubric(db) -> list[dict]:
    """Load the active playbook rubric criteria from the database.

    Falls back to DEFAULT_RUBRIC if no active playbook is found.

    Args:
        db: SQLAlchemy database session.

    Returns:
        List of rubric category dicts.
    """
    playbook = (
        db.query(Playbook)
        .filter(Playbook.is_active.is_(True))
        .order_by(Playbook.version.desc())
        .first()
    )

    if playbook and playbook.criteria:
        logger.info("Using playbook '%s' (v%d) for scoring", playbook.name, playbook.version)
        return playbook.criteria

    logger.info("No active playbook found, using default rubric")
    return DEFAULT_RUBRIC
