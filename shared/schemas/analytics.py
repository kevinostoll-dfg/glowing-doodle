"""Analytics schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class DateRange(BaseModel):
    """Date range filter."""

    start_date: date
    end_date: date


class AnalyticsQuery(BaseModel):
    """Analytics query parameters."""

    shop_id: int
    start_date: date
    end_date: date
    granularity: str = "day"  # day, week, month


class ShopAnalytics(BaseModel):
    """Aggregated shop analytics response."""

    shop_id: int
    period_start: datetime
    period_end: datetime
    total_calls: int = 0
    inbound_calls: int = 0
    outbound_calls: int = 0
    missed_calls: int = 0
    ai_handled_calls: int = 0
    avg_duration: float = 0.0
    avg_score: float | None = None
    sentiment_distribution: dict[str, int] = {}
    lead_source_breakdown: dict[str, int] = {}
    daily_trends: list[dict] = []
