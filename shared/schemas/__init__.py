"""Pydantic schemas for the Call Intelligence Platform."""

from shared.schemas.analytics import AnalyticsQuery, DateRange, ShopAnalytics
from shared.schemas.call import CallCreate, CallListResponse, CallResponse, CallUpdate
from shared.schemas.common import ErrorResponse, HealthResponse, PaginatedResponse
from shared.schemas.playbook import PlaybookCreate, PlaybookResponse, RubricCategory
from shared.schemas.shop import ShopCreate, ShopResponse, ShopUpdate

__all__ = [
    "AnalyticsQuery",
    "CallCreate",
    "CallListResponse",
    "CallResponse",
    "CallUpdate",
    "DateRange",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PlaybookCreate",
    "PlaybookResponse",
    "RubricCategory",
    "ShopAnalytics",
    "ShopCreate",
    "ShopResponse",
    "ShopUpdate",
]
