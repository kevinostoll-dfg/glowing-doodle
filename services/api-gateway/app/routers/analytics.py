"""Analytics endpoints."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.auth import get_current_user
from shared.database import get_db
from shared.models.user import User
from shared.schemas.analytics import ShopAnalytics

from app.services.analytics_service import (
    get_advisor_leaderboard,
    get_shop_analytics,
    get_trends,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _default_start() -> date:
    """Default start date: 30 days ago."""
    return date.today() - timedelta(days=30)


def _default_end() -> date:
    """Default end date: today."""
    return date.today()


# --- response schema for trends ---
class TrendPoint(BaseModel):
    period: str
    total_calls: int = 0
    inbound_calls: int = 0
    outbound_calls: int = 0
    missed_calls: int = 0
    avg_duration: float = 0.0
    avg_score: float | None = None


class TrendsResponse(BaseModel):
    shop_id: int
    granularity: str
    data: list[TrendPoint]


# --- response schema for advisor leaderboard ---
class AdvisorStats(BaseModel):
    handled_by: str | None
    total_calls: int = 0
    avg_score: float | None = None
    avg_duration: float = 0.0


class AdvisorLeaderboardResponse(BaseModel):
    shop_id: int
    advisors: list[AdvisorStats]


def _check_shop_access(current_user: User, shop_id: int) -> None:
    if current_user.role != "admin" and current_user.shop_id != shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/shop/{shop_id}", response_model=ShopAnalytics)
def shop_metrics(
    shop_id: int,
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=_default_end),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated metrics for a shop within a date range."""
    _check_shop_access(current_user, shop_id)
    return get_shop_analytics(db, shop_id, start_date, end_date)


@router.get("/trends/{shop_id}", response_model=TrendsResponse)
def trends(
    shop_id: int,
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=_default_end),
    granularity: str = Query("day", description="day, week, or month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get call trends grouped by day, week, or month."""
    _check_shop_access(current_user, shop_id)

    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="granularity must be day, week, or month",
        )

    data = get_trends(db, shop_id, start_date, end_date, granularity)
    return TrendsResponse(shop_id=shop_id, granularity=granularity, data=data)


@router.get("/advisors/{shop_id}", response_model=AdvisorLeaderboardResponse)
def advisors(
    shop_id: int,
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=_default_end),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the advisor leaderboard ranked by average score."""
    _check_shop_access(current_user, shop_id)
    rows = get_advisor_leaderboard(db, shop_id, start_date, end_date)
    return AdvisorLeaderboardResponse(shop_id=shop_id, advisors=rows)
