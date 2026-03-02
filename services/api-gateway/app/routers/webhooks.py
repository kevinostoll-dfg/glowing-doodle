"""Twilio webhook endpoints.

These do NOT require API-key authentication but DO validate the
Twilio request signature.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database import get_db
from shared.models.call import Call
from shared.models.phone_number import PhoneNumber

from app.dependencies import validate_twilio_post

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _twiml(body: str) -> Response:
    """Return a TwiML XML response."""
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'
    return Response(content=xml, media_type="application/xml")


# ------------------------------------------------------------------ voice
@router.post("/voice")
async def voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Direction: str = Form("inbound"),
    CallerName: str = Form(None),
    _sig: None = Depends(validate_twilio_post),
    db: Session = Depends(get_db),
):
    """Twilio voice webhook – called when a new call arrives.

    Creates a Call record and returns TwiML instructing Twilio to record
    the call and connect it.
    """
    settings = get_settings()

    # Resolve the shop via the dialed phone number.
    phone_entry = db.query(PhoneNumber).filter(PhoneNumber.phone_number == To).first()
    if not phone_entry:
        logger.warning("No phone number mapping for %s", To)
        return _twiml("<Say>We're sorry, this number is not configured.</Say><Hangup/>")

    # Create the call record.
    call = Call(
        shop_id=phone_entry.shop_id,
        twilio_call_sid=CallSid,
        direction=Direction.lower() if Direction else "inbound",
        status="ringing",
        from_number=From,
        to_number=To,
        caller_name=CallerName,
        start_time=datetime.utcnow(),
    )
    db.add(call)
    db.commit()

    # Build TwiML: record and dial the shop's main number.
    shop = phone_entry.shop
    twiml_body = "<Say>Thank you for calling. This call may be recorded for quality purposes.</Say>"
    twiml_body += (
        f'<Record action="/webhooks/recording" recordingStatusCallback="/webhooks/recording"'
        f' timeout="10" transcribe="false" />'
    )
    if shop and shop.phone_number:
        twiml_body += f"<Dial>{shop.phone_number}</Dial>"
    else:
        twiml_body += "<Say>No one is available to take your call. Please try again later.</Say><Hangup/>"

    return _twiml(twiml_body)


# ------------------------------------------------------------------ status
@router.post("/status")
async def status_callback(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str = Form(None),
    _sig: None = Depends(validate_twilio_post),
    db: Session = Depends(get_db),
):
    """Twilio status callback – called when the call status changes."""
    call = db.query(Call).filter(Call.twilio_call_sid == CallSid).first()
    if not call:
        logger.warning("Status callback for unknown CallSid: %s", CallSid)
        return Response(status_code=204)

    # Map Twilio statuses to our internal statuses.
    status_map = {
        "queued": "initiated",
        "ringing": "ringing",
        "in-progress": "in-progress",
        "completed": "completed",
        "busy": "missed",
        "no-answer": "missed",
        "canceled": "missed",
        "failed": "missed",
    }
    call.status = status_map.get(CallStatus.lower(), CallStatus.lower())

    if CallDuration:
        call.duration_seconds = int(CallDuration)

    if call.status in ("completed", "missed"):
        call.end_time = datetime.utcnow()

    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------------ recording
@router.post("/recording")
async def recording_callback(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingSid: str = Form(None),
    RecordingStatus: str = Form(None),
    _sig: None = Depends(validate_twilio_post),
    db: Session = Depends(get_db),
):
    """Twilio recording callback – called when a recording is ready."""
    call = db.query(Call).filter(Call.twilio_call_sid == CallSid).first()
    if not call:
        logger.warning("Recording callback for unknown CallSid: %s", CallSid)
        return Response(status_code=204)

    # Store the recording URL (Twilio provides a .wav/.mp3 download link).
    call.recording_url = RecordingUrl
    call.transcript_status = "pending"
    db.commit()

    logger.info(
        "Recording received for call %s (SID %s): %s",
        call.id,
        CallSid,
        RecordingUrl,
    )

    return Response(status_code=204)
