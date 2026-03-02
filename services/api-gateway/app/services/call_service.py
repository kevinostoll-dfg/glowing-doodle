"""Call business-logic service layer."""

import logging
import math
from datetime import date, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from twilio.rest import Client as TwilioClient

from shared.config import get_settings
from shared.models.call import Call
from shared.schemas.call import CallCreate, CallListResponse, CallResponse, CallUpdate

logger = logging.getLogger(__name__)


def list_calls(
    db: Session,
    *,
    shop_id: int | None = None,
    direction: str | None = None,
    call_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> CallListResponse:
    """Return a paginated, filterable list of calls."""
    query = db.query(Call)

    if shop_id is not None:
        query = query.filter(Call.shop_id == shop_id)
    if direction:
        query = query.filter(Call.direction == direction)
    if call_status:
        query = query.filter(Call.status == call_status)
    if start_date:
        query = query.filter(Call.start_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Call.start_time <= datetime.combine(end_date, datetime.max.time()))
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Call.caller_name.ilike(term),
                Call.from_number.ilike(term),
                Call.to_number.ilike(term),
            )
        )

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))

    calls = (
        query.order_by(Call.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CallListResponse(
        items=[CallResponse.model_validate(c) for c in calls],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_call(db: Session, call_id: int) -> Call | None:
    """Fetch a single call by primary key, eagerly loading participants."""
    return (
        db.query(Call)
        .options(joinedload(Call.participants))
        .filter(Call.id == call_id)
        .first()
    )


def create_call(db: Session, payload: CallCreate) -> Call:
    """Insert a new call record."""
    call = Call(
        shop_id=payload.shop_id,
        direction=payload.direction,
        from_number=payload.from_number,
        to_number=payload.to_number,
        caller_name=payload.caller_name,
        handled_by=payload.handled_by,
        status="initiated",
        start_time=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def update_call(db: Session, call: Call, payload: CallUpdate) -> Call:
    """Apply partial updates to an existing call."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)
    db.commit()
    db.refresh(call)
    return call


def initiate_outbound_call(
    db: Session,
    shop_id: int,
    from_number: str,
    to_number: str,
    status_callback_url: str | None = None,
) -> Call:
    """Place an outbound call via the Twilio REST API and persist the record.

    Args:
        db: Database session.
        shop_id: The shop initiating the call.
        from_number: Caller ID (must be a verified Twilio number).
        to_number: Destination phone number.
        status_callback_url: Optional URL for Twilio status callbacks.

    Returns:
        The newly created Call ORM instance.
    """
    settings = get_settings()

    client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)

    twilio_params: dict = {
        "to": to_number,
        "from_": from_number,
        "record": True,
    }
    if status_callback_url:
        twilio_params["status_callback"] = status_callback_url
        twilio_params["status_callback_event"] = ["initiated", "ringing", "answered", "completed"]

    twilio_call = client.calls.create(**twilio_params)

    call = Call(
        shop_id=shop_id,
        twilio_call_sid=twilio_call.sid,
        direction="outbound",
        status="initiated",
        from_number=from_number,
        to_number=to_number,
        start_time=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    logger.info("Outbound call initiated: %s -> %s (SID: %s)", from_number, to_number, twilio_call.sid)
    return call
