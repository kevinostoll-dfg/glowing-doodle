"""Generate analytics reports (daily/weekly) for all shops."""

import argparse
import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.call_metrics import CallMetrics
from shared.models.shop import Shop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def generate_daily_metrics(db: Session, shop: Shop, report_date: date) -> dict:
    """Generate daily metrics for a shop."""
    start = datetime.combine(report_date, datetime.min.time())
    end = datetime.combine(report_date, datetime.max.time())

    calls = db.query(Call).filter(
        Call.shop_id == shop.id,
        Call.start_time >= start,
        Call.start_time <= end,
    ).all()

    total = len(calls)
    inbound = sum(1 for c in calls if c.direction == "inbound")
    outbound = sum(1 for c in calls if c.direction == "outbound")
    missed = sum(1 for c in calls if c.status == "missed")
    ai_handled = sum(1 for c in calls if c.handled_by == "ai")

    durations = [c.duration_seconds for c in calls if c.duration_seconds]
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    scores = [c.ai_score for c in calls if c.ai_score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    sentiments = {}
    for c in calls:
        if c.sentiment:
            sentiments[c.sentiment] = sentiments.get(c.sentiment, 0) + 1

    # Upsert metrics
    existing = db.query(CallMetrics).filter(
        CallMetrics.shop_id == shop.id,
        CallMetrics.date == report_date,
    ).first()

    if existing:
        metrics = existing
    else:
        metrics = CallMetrics(shop_id=shop.id, date=report_date)
        db.add(metrics)

    metrics.total_calls = total
    metrics.inbound_calls = inbound
    metrics.outbound_calls = outbound
    metrics.missed_calls = missed
    metrics.ai_handled_calls = ai_handled
    metrics.avg_duration = avg_duration
    metrics.avg_score = avg_score
    metrics.sentiment_distribution = sentiments
    db.commit()

    return {
        "shop": shop.name,
        "date": str(report_date),
        "total_calls": total,
        "inbound": inbound,
        "outbound": outbound,
        "missed": missed,
        "ai_handled": ai_handled,
        "avg_duration": round(avg_duration, 1),
        "avg_score": round(avg_score, 1) if avg_score else None,
    }


def generate_report(db: Session, report_type: str, report_date: date | None = None) -> None:
    """Generate report for all shops."""
    shops = db.query(Shop).all()

    if report_type == "daily":
        target_date = report_date or (date.today() - timedelta(days=1))
        logger.info(f"Generating daily report for {target_date}")
        results = []
        for shop in shops:
            metrics = generate_daily_metrics(db, shop, target_date)
            results.append(metrics)
            logger.info(f"  {shop.name}: {metrics['total_calls']} calls, avg score {metrics['avg_score']}")

        report = {"type": "daily", "date": str(target_date), "shops": results}

    elif report_type == "weekly":
        end_date = report_date or (date.today() - timedelta(days=1))
        start_date = end_date - timedelta(days=6)
        logger.info(f"Generating weekly report for {start_date} to {end_date}")

        results = []
        for shop in shops:
            daily_metrics = []
            current = start_date
            while current <= end_date:
                m = generate_daily_metrics(db, shop, current)
                daily_metrics.append(m)
                current += timedelta(days=1)

            total_calls = sum(d["total_calls"] for d in daily_metrics)
            scores = [d["avg_score"] for d in daily_metrics if d["avg_score"] is not None]
            weekly_avg_score = sum(scores) / len(scores) if scores else None

            results.append({
                "shop": shop.name,
                "period": f"{start_date} to {end_date}",
                "total_calls": total_calls,
                "avg_score": round(weekly_avg_score, 1) if weekly_avg_score else None,
                "daily_breakdown": daily_metrics,
            })
            logger.info(f"  {shop.name}: {total_calls} calls over 7 days")

        report = {
            "type": "weekly",
            "period_start": str(start_date),
            "period_end": str(end_date),
            "shops": results,
        }

    else:
        logger.error(f"Unknown report type: {report_type}")
        return

    logger.info(f"Report generated:\n{json.dumps(report, indent=2)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate analytics reports")
    parser.add_argument("--type", required=True, choices=["daily", "weekly"], help="Report type")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD), defaults to yesterday")
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else None

    db = SessionLocal()
    try:
        generate_report(db, args.type, report_date)
    finally:
        db.close()


if __name__ == "__main__":
    main()
