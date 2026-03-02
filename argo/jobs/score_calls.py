"""Score unscored calls using Claude API with rate limiting."""

import argparse
import json
import logging
import time
from datetime import date, datetime, timedelta

import anthropic
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.playbook import Playbook

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 1.0  # seconds between API calls


def get_scoring_prompt(transcript: str, criteria: list, shop_name: str) -> str:
    """Build scoring prompt for Claude."""
    criteria_text = "\n".join(
        f"- {c['name']} (weight: {c['weight']}): {c['description']}\n"
        f"  Criteria: {', '.join(c['criteria'])}"
        for c in criteria
    )

    return f"""Analyze this auto repair shop phone call transcript and score the service advisor's performance.

Shop: {shop_name}

## Scoring Rubric
{criteria_text}

## Transcript
{transcript}

## Instructions
Score each category from 0-100. Calculate the weighted overall score.
Identify the caller's sentiment, intent, and key discussion points.
Provide specific coaching notes for improvement.

Respond with valid JSON only:
{{
  "overall_score": <float>,
  "category_scores": {{
    "<category_name>": <int>,
    ...
  }},
  "sentiment": "<positive|neutral|negative>",
  "caller_intent": "<string>",
  "key_points": ["<point1>", "<point2>", ...],
  "coaching_notes": "<string>",
  "is_new_customer": "<yes|no|unknown>"
}}"""


def score_call(client: anthropic.Anthropic, call: Call, criteria: list, shop_name: str) -> dict:
    """Score a single call using Claude API."""
    prompt = get_scoring_prompt(call.transcript, criteria, shop_name)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.content[0].text)


def process_calls(db: Session, shop_id: int | None, start: date, end: date) -> None:
    """Process and score unscored calls."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Get active playbook
    playbook = db.query(Playbook).filter(Playbook.is_active.is_(True)).first()
    if not playbook:
        logger.error("No active playbook found")
        return

    # Query unscored calls with transcripts
    query = db.query(Call).filter(
        Call.transcript.isnot(None),
        Call.analysis_status.in_(["pending", "failed"]),
        Call.start_time >= datetime.combine(start, datetime.min.time()),
        Call.start_time <= datetime.combine(end, datetime.max.time()),
    )
    if shop_id:
        query = query.filter(Call.shop_id == shop_id)

    calls = query.all()
    logger.info(f"Found {len(calls)} unscored calls to process")

    scored = 0
    failed = 0
    for call in calls:
        try:
            call.analysis_status = "processing"
            db.commit()

            shop_name = call.shop.name if call.shop else "Unknown Shop"
            result = score_call(client, call, playbook.criteria, shop_name)

            call.ai_score = result["overall_score"]
            call.sentiment = result.get("sentiment")
            call.caller_intent = result.get("caller_intent")
            call.key_points = result.get("key_points", [])
            call.coaching_notes = result.get("coaching_notes")
            call.is_new_customer = result.get("is_new_customer", "unknown")
            call.analysis_status = "completed"
            db.commit()

            scored += 1
            logger.info(f"Scored call {call.id}: {call.ai_score}")
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            logger.error(f"Failed to score call {call.id}: {e}")
            call.analysis_status = "failed"
            db.commit()
            failed += 1

    logger.info(f"Scoring complete: {scored} scored, {failed} failed out of {len(calls)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score calls using Claude API")
    parser.add_argument("--shop-id", type=int, help="Filter by shop ID")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--date",
        type=str,
        choices=["today", "yesterday"],
        help="Shortcut for date range",
    )
    args = parser.parse_args()

    today = date.today()
    if args.date == "yesterday":
        start = end = today - timedelta(days=1)
    elif args.date == "today":
        start = end = today
    elif args.start_date and args.end_date:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
    else:
        start = end = today - timedelta(days=1)

    db = SessionLocal()
    try:
        process_calls(db, args.shop_id, start, end)
    finally:
        db.close()


if __name__ == "__main__":
    main()
