"""Transcription tasks for processing call recordings."""

import asyncio
import logging

from app.celery_app import celery
from app.integrations.deepgram_client import transcribe_audio
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.call_participant import CallParticipant

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    name="app.tasks.transcription.transcribe_call",
    max_retries=3,
    default_retry_delay=30,
)
def transcribe_call(self, call_id: int) -> dict:
    """Transcribe a call recording using Deepgram.

    Downloads the recording from the call's recording_url, sends it to
    Deepgram for transcription with diarization and sentiment analysis,
    then saves the results back to the database.

    On success, chains to the analyze_call task.

    Args:
        call_id: The database ID of the call to transcribe.

    Returns:
        Dict with call_id and transcript_status.
    """
    logger.info("Starting transcription for call %d", call_id)

    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            logger.error("Call %d not found", call_id)
            return {"call_id": call_id, "transcript_status": "failed", "error": "Call not found"}

        if not call.recording_url:
            logger.error("Call %d has no recording URL", call_id)
            call.transcript_status = "failed"
            db.commit()
            return {"call_id": call_id, "transcript_status": "failed", "error": "No recording URL"}

        # Mark as processing
        call.transcript_status = "processing"
        db.commit()

        try:
            # Run the async transcription in a synchronous context
            result = asyncio.get_event_loop().run_until_complete(
                transcribe_audio(call.recording_url)
            )
        except RuntimeError:
            # No event loop running; create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    transcribe_audio(call.recording_url)
                )
            finally:
                loop.close()

        # Save transcript text to the Call record
        call.transcript = result.transcript
        call.transcript_status = "completed"

        # Create CallParticipant records for each detected speaker
        for speaker_info in result.speakers:
            # Find utterances for this speaker
            speaker_utterances = [
                {
                    "text": u.text,
                    "start": u.start,
                    "end": u.end,
                    "confidence": u.confidence,
                }
                for u in result.utterances
                if u.speaker == speaker_info["speaker"]
            ]

            participant = CallParticipant(
                call_id=call_id,
                speaker_label=speaker_info["label"],
                role=_infer_role(speaker_info["speaker"]),
                utterances=speaker_utterances,
                total_talk_time_seconds=speaker_info["total_talk_time"],
            )
            db.add(participant)

        db.commit()

        logger.info(
            "Transcription completed for call %d: %d characters, %d speakers",
            call_id,
            len(result.transcript),
            len(result.speakers),
        )

        # Chain to analysis task on success
        from app.tasks.analysis import analyze_call

        analyze_call.delay(call_id)

        return {"call_id": call_id, "transcript_status": "completed"}

    except Exception as exc:
        db.rollback()
        logger.exception("Transcription failed for call %d: %s", call_id, exc)

        # Update status to failed
        try:
            call = db.query(Call).filter(Call.id == call_id).first()
            if call:
                call.transcript_status = "failed"
                db.commit()
        except Exception:
            logger.exception("Failed to update transcript_status for call %d", call_id)

        # Retry with exponential backoff
        raise self.retry(exc=exc)

    finally:
        db.close()


def _infer_role(speaker_index: int) -> str:
    """Infer the participant role based on speaker index.

    Speaker 0 is typically the service advisor (the person who answered),
    and subsequent speakers are assumed to be customers.

    Args:
        speaker_index: The zero-based speaker index from diarization.

    Returns:
        'advisor' or 'customer'.
    """
    return "advisor" if speaker_index == 0 else "customer"
