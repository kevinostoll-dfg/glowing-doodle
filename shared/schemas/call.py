"""Call schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from shared.schemas.common import PaginatedResponse


class CallCreate(BaseModel):
    """Schema for creating a call record."""

    shop_id: int
    direction: str
    from_number: str
    to_number: str
    caller_name: str | None = None
    handled_by: str | None = None


class CallUpdate(BaseModel):
    """Schema for updating a call record."""

    status: str | None = None
    end_time: datetime | None = None
    duration_seconds: int | None = None
    recording_url: str | None = None
    transcript: str | None = None
    transcript_status: str | None = None
    ai_score: float | None = None
    sentiment: str | None = None
    caller_intent: str | None = None
    key_points: list[Any] | None = None
    coaching_notes: str | None = None
    analysis_status: str | None = None
    is_new_customer: str | None = None


class CallResponse(BaseModel):
    """Schema for call response."""

    id: int
    shop_id: int
    twilio_call_sid: str | None
    direction: str
    status: str
    from_number: str | None
    to_number: str | None
    caller_name: str | None
    start_time: datetime | None
    end_time: datetime | None
    duration_seconds: int | None
    recording_url: str | None
    transcript: str | None
    transcript_status: str | None
    ai_score: float | None
    sentiment: str | None
    caller_intent: str | None
    key_points: list[Any] | None
    coaching_notes: str | None
    analysis_status: str | None
    is_new_customer: str | None
    handled_by: str | None
    ai_agent_language: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallListResponse(PaginatedResponse[CallResponse]):
    """Paginated call list response."""

    pass
