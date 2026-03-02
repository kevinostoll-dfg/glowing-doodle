"""Call routing endpoints for Twilio webhooks."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from twilio.rest import Client as TwilioClient

from app.business_hours import check_business_hours
from app.twiml_builder import (
    build_ai_agent_twiml,
    build_forward_twiml,
    build_greeting_twiml,
    build_voicemail_twiml,
)
from shared.config import get_settings
from shared.database import get_db
from shared.models.call import Call
from shared.models.phone_number import PhoneNumber
from shared.models.shop import Shop
from shared.utils import format_phone

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _twiml_response(twiml: str) -> Response:
    """Return a TwiML XML response."""
    return Response(content=twiml, media_type="application/xml")


def _get_twilio_client() -> TwilioClient:
    """Create a Twilio REST API client."""
    return TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)


def _lookup_shop_by_number(to_number: str, db: Session) -> Shop | None:
    """Find the shop associated with a Twilio phone number."""
    phone_record = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.phone_number == format_phone(to_number))
        .filter(PhoneNumber.is_active.is_(True))
        .first()
    )
    if phone_record:
        return db.query(Shop).filter(Shop.id == phone_record.shop_id).first()
    return None


@router.post("/inbound")
async def inbound_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallerName: str = Form(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Receive an inbound call from Twilio.

    Looks up the shop by the called number, checks business hours,
    and routes to human (Dial) or AI agent (Connect Stream).
    """
    logger.info("Inbound call %s from %s to %s", CallSid, From, To)

    # Look up shop by the dialed number
    shop = _lookup_shop_by_number(To, db)
    if not shop:
        logger.warning("No shop found for number %s", To)
        twiml = build_voicemail_twiml()
        return _twiml_response(twiml)

    # Create call record in database
    call = Call(
        shop_id=shop.id,
        twilio_call_sid=CallSid,
        direction="inbound",
        status="ringing",
        from_number=format_phone(From),
        to_number=format_phone(To),
        caller_name=CallerName,
        start_time=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # Check if the shop is currently open
    is_open = check_business_hours(shop)

    if is_open and shop.phone_number:
        # During business hours: forward to the shop's phone with a greeting
        logger.info("Routing call %s to human at %s", CallSid, shop.phone_number)
        call.handled_by = "human"
        db.commit()
        twiml = build_forward_twiml(
            shop_phone=shop.phone_number,
            caller_id=format_phone(To),
        )
    else:
        # After hours or no shop phone: route to AI voice agent
        logger.info("Routing call %s to AI agent for shop %s", CallSid, shop.name)
        call.handled_by = "ai"
        call.ai_agent_language = "en"
        db.commit()

        # Build WebSocket URL for the voice agent service
        ws_url = f"wss://voice-agent:8002/ws/voice/{call.id}"
        twiml = build_ai_agent_twiml(call_id=str(call.id), ws_url=ws_url)

    return _twiml_response(twiml)


@router.post("/outbound")
async def outbound_call(
    request: Request,
    to_number: str = Form(...),
    from_number: str = Form(...),
    shop_id: int = Form(...),
    db: Session = Depends(get_db),
) -> dict:
    """Initiate an outbound call via Twilio REST API.

    Creates a call record and triggers Twilio to place the call.
    """
    logger.info("Outbound call request from shop %d to %s", shop_id, to_number)

    # Verify the shop exists
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    formatted_to = format_phone(to_number)
    formatted_from = format_phone(from_number)

    # Create call record
    call = Call(
        shop_id=shop_id,
        direction="outbound",
        status="initiated",
        from_number=formatted_from,
        to_number=formatted_to,
        start_time=datetime.utcnow(),
        handled_by="human",
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # Place the call via Twilio
    try:
        client = _get_twilio_client()
        twilio_call = client.calls.create(
            to=formatted_to,
            from_=formatted_from,
            url=f"{request.base_url}outbound-twiml",
            status_callback=f"{request.base_url}status-callback",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=True,
            recording_status_callback=f"{request.base_url}recording-callback",
        )
        call.twilio_call_sid = twilio_call.sid
        db.commit()
    except Exception as e:
        logger.error("Failed to place outbound call: %s", e)
        call.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Failed to place call via Twilio")

    return {
        "call_id": call.id,
        "twilio_call_sid": twilio_call.sid,
        "status": "initiated",
    }


@router.post("/status-callback")
async def status_callback(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str = Form(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Twilio status callback - updates call status and duration in DB.

    Called by Twilio when call status changes (initiated, ringing,
    in-progress, completed, busy, no-answer, canceled, failed).
    """
    logger.info("Status callback: %s -> %s", CallSid, CallStatus)

    call = db.query(Call).filter(Call.twilio_call_sid == CallSid).first()
    if not call:
        logger.warning("No call found for SID %s", CallSid)
        return _twiml_response("<Response/>")

    # Map Twilio statuses to our status values
    status_map = {
        "initiated": "initiated",
        "ringing": "ringing",
        "in-progress": "in-progress",
        "completed": "completed",
        "busy": "missed",
        "no-answer": "missed",
        "canceled": "missed",
        "failed": "missed",
    }
    call.status = status_map.get(CallStatus, CallStatus)

    if CallDuration:
        call.duration_seconds = int(CallDuration)

    if CallStatus in ("completed", "busy", "no-answer", "canceled", "failed"):
        call.end_time = datetime.utcnow()

    db.commit()

    return _twiml_response("<Response/>")


@router.post("/recording-callback")
async def recording_callback(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingSid: str = Form(...),
    RecordingDuration: str = Form(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Twilio recording callback - saves recording URL and enqueues transcription.

    Called by Twilio when a recording is available. Stores the URL
    and dispatches a Celery task to transcribe the recording.
    """
    logger.info("Recording callback: %s, recording %s", CallSid, RecordingSid)

    call = db.query(Call).filter(Call.twilio_call_sid == CallSid).first()
    if not call:
        logger.warning("No call found for SID %s", CallSid)
        return _twiml_response("<Response/>")

    # Store the recording URL (Twilio provides a .wav URL)
    call.recording_url = f"{RecordingUrl}.wav"
    call.transcript_status = "processing"

    if RecordingDuration and not call.duration_seconds:
        call.duration_seconds = int(RecordingDuration)

    db.commit()

    # Enqueue transcription task via Celery
    try:
        from celery import Celery

        celery_app = Celery("calliq", broker=settings.redis_url)
        celery_app.send_task(
            "tasks.transcribe_recording",
            args=[call.id, call.recording_url],
            queue="transcription",
        )
        logger.info("Enqueued transcription task for call %d", call.id)
    except Exception as e:
        logger.error("Failed to enqueue transcription task: %s", e)
        call.transcript_status = "failed"
        db.commit()

    return _twiml_response("<Response/>")
