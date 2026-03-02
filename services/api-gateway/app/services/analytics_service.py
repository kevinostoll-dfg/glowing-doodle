"""Analytics business-logic service layer."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from shared.models.call import Call
from shared.schemas.analytics import ShopAnalytics


def get_shop_analytics(
    db: Session,
    shop_id: int,
    start_date: date,
    end_date: date,
) -> ShopAnalytics:
    """Compute aggregated metrics for a shop over the given date range."""
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    base = db.query(Call).filter(
        Call.shop_id == shop_id,
        Call.start_time >= start_dt,
        Call.start_time <= end_dt,
    )

    total_calls = base.count()

    stats = base.with_entities(
        func.count().label("total"),
        func.sum(case((Call.direction == "inbound", 1), else_=0)).label("inbound"),
        func.sum(case((Call.direction == "outbound", 1), else_=0)).label("outbound"),
        func.sum(case((Call.status == "missed", 1), else_=0)).label("missed"),
        func.sum(case((Call.handled_by == "ai", 1), else_=0)).label("ai_handled"),
        func.avg(Call.duration_seconds).label("avg_dur"),
        func.avg(Call.ai_score).label("avg_score"),
    ).first()

    # Sentiment distribution
    sentiment_rows = (
        base.with_entities(Call.sentiment, func.count())
        .filter(Call.sentiment.isnot(None))
        .group_by(Call.sentiment)
        .all()
    )
    sentiment_dist = {s: c for s, c in sentiment_rows}

    # Daily trends (always by day for the overview endpoint)
    trend_rows = (
        base.with_entities(
            func.date_trunc("day", Call.start_time).label("period"),
            func.count().label("cnt"),
        )
        .group_by("period")
        .order_by("period")
        .all()
    )
    daily_trends = [
        {"date": row.period.isoformat(), "total_calls": row.cnt}
        for row in trend_rows
    ]

    return ShopAnalytics(
        shop_id=shop_id,
        period_start=start_dt,
        period_end=end_dt,
        total_calls=stats.total or 0,
        inbound_calls=stats.inbound or 0,
        outbound_calls=stats.outbound or 0,
        missed_calls=stats.missed or 0,
        ai_handled_calls=stats.ai_handled or 0,
        avg_duration=float(stats.avg_dur or 0),
        avg_score=float(stats.avg_score) if stats.avg_score is not None else None,
        sentiment_distribution=sentiment_dist,
        daily_trends=daily_trends,
    )


def get_trends(
    db: Session,
    shop_id: int,
    start_date: date,
    end_date: date,
    granularity: str = "day",
) -> list[dict[str, Any]]:
    """Return time-series call data bucketed by the requested granularity.

    Uses PostgreSQL's ``date_trunc`` for grouping.
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    period_col = func.date_trunc(granularity, Call.start_time).label("period")

    rows = (
        db.query(
            period_col,
            func.count().label("total_calls"),
            func.sum(case((Call.direction == "inbound", 1), else_=0)).label("inbound_calls"),
            func.sum(case((Call.direction == "outbound", 1), else_=0)).label("outbound_calls"),
            func.sum(case((Call.status == "missed", 1), else_=0)).label("missed_calls"),
            func.avg(Call.duration_seconds).label("avg_duration"),
            func.avg(Call.ai_score).label("avg_score"),
        )
        .filter(
            Call.shop_id == shop_id,
            Call.start_time >= start_dt,
            Call.start_time <= end_dt,
        )
        .group_by(period_col)
        .order_by(period_col)
        .all()
    )

    return [
        {
            "period": row.period.isoformat(),
            "total_calls": row.total_calls or 0,
            "inbound_calls": row.inbound_calls or 0,
            "outbound_calls": row.outbound_calls or 0,
            "missed_calls": row.missed_calls or 0,
            "avg_duration": float(row.avg_duration or 0),
            "avg_score": float(row.avg_score) if row.avg_score is not None else None,
        }
        for row in rows
    ]


def get_advisor_leaderboard(
    db: Session,
    shop_id: int,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Return advisor stats grouped by ``handled_by``, sorted by avg score descending."""
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    rows = (
        db.query(
            Call.handled_by,
            func.count().label("total_calls"),
            func.avg(Call.ai_score).label("avg_score"),
            func.avg(Call.duration_seconds).label("avg_duration"),
        )
        .filter(
            Call.shop_id == shop_id,
            Call.start_time >= start_dt,
            Call.start_time <= end_dt,
            Call.handled_by.isnot(None),
        )
        .group_by(Call.handled_by)
        .order_by(func.avg(Call.ai_score).desc().nulls_last())
        .all()
    )

    return [
        {
            "handled_by": row.handled_by,
            "total_calls": row.total_calls or 0,
            "avg_score": float(row.avg_score) if row.avg_score is not None else None,
            "avg_duration": float(row.avg_duration or 0),
        }
        for row in rows
    ]
