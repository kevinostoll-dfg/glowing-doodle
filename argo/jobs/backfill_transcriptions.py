"""Backfill transcriptions for calls that have recordings but no transcript."""

import argparse
import logging
import time

import httpx
from deepgram import DeepgramClient, PrerecordedOptions

from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.call_participant import CallParticipant

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 2.0


def transcribe_recording(deepgram: DeepgramClient, recording_url: str) -> dict:
    """Transcribe a recording URL using Deepgram."""
    options = PrerecordedOptions(
        model="nova-3",
        diarize=True,
        sentiment=True,
        detect_language=True,
        punctuate=True,
        utterances=True,
    )

    response = deepgram.listen.rest.v("1").transcribe_url(
        {"url": recording_url}, options
    )

    result = response.to_dict()

    transcript = ""
    if result.get("results", {}).get("channels"):
        channel = result["results"]["channels"][0]
        if channel.get("alternatives"):
            transcript = channel["alternatives"][0].get("transcript", "")

    speakers = {}
    if result.get("results", {}).get("utterances"):
        for utt in result["results"]["utterances"]:
            speaker = utt.get("speaker", 0)
            label = f"Speaker {speaker}"
            if label not in speakers:
                speakers[label] = {"utterances": [], "total_time": 0.0}
            speakers[label]["utterances"].append({
                "text": utt.get("transcript", ""),
                "start": utt.get("start", 0),
                "end": utt.get("end", 0),
            })
            speakers[label]["total_time"] += utt.get("end", 0) - utt.get("start", 0)

    language = None
    if result.get("results", {}).get("channels"):
        channel = result["results"]["channels"][0]
        language = channel.get("detected_language")

    return {
        "transcript": transcript,
        "speakers": speakers,
        "language": language,
    }


def backfill(shop_id: int | None = None, limit: int = 100) -> None:
    """Backfill transcriptions for calls missing them."""
    settings = get_settings()
    deepgram = DeepgramClient(settings.deepgram_api_key)
    db = SessionLocal()

    try:
        query = db.query(Call).filter(
            Call.recording_url.isnot(None),
            Call.transcript.is_(None),
        )
        if shop_id:
            query = query.filter(Call.shop_id == shop_id)
        query = query.order_by(Call.created_at.desc()).limit(limit)

        calls = query.all()
        logger.info(f"Found {len(calls)} calls to backfill")

        success = 0
        failed = 0
        for call in calls:
            try:
                call.transcript_status = "processing"
                db.commit()

                result = transcribe_recording(deepgram, call.recording_url)

                call.transcript = result["transcript"]
                call.transcript_status = "completed"
                if result.get("language"):
                    call.ai_agent_language = result["language"]

                # Create participant records
                for label, data in result.get("speakers", {}).items():
                    participant = CallParticipant(
                        call_id=call.id,
                        speaker_label=label,
                        role="unknown",
                        utterances=data["utterances"],
                        total_talk_time_seconds=data["total_time"],
                    )
                    db.add(participant)

                db.commit()
                success += 1
                logger.info(f"Transcribed call {call.id}")
                time.sleep(RATE_LIMIT_DELAY)

            except Exception as e:
                logger.error(f"Failed to transcribe call {call.id}: {e}")
                call.transcript_status = "failed"
                db.commit()
                failed += 1

        logger.info(f"Backfill complete: {success} transcribed, {failed} failed")

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill call transcriptions")
    parser.add_argument("--shop-id", type=int, help="Filter by shop ID")
    parser.add_argument("--limit", type=int, default=100, help="Max calls to process")
    args = parser.parse_args()

    backfill(args.shop_id, args.limit)


if __name__ == "__main__":
    main()
