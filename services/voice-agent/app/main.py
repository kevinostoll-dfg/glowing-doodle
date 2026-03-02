"""Voice Agent service - AI-powered voice assistant via OpenAI Realtime API."""

import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.agent import VoiceAgent
from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.shop import Shop
from shared.schemas.common import HealthResponse

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Agent Service",
    description="AI voice agent using OpenAI Realtime API for Twilio media streams",
    version="0.1.0",
)


def _get_call_and_shop(call_id: int) -> tuple[Call | None, Shop | None]:
    """Look up a call and its associated shop from the database."""
    db: Session = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return None, None
        shop = db.query(Shop).filter(Shop.id == call.shop_id).first()
        return call, shop
    finally:
        db.close()


@app.websocket("/ws/voice/{call_id}")
async def voice_websocket(websocket: WebSocket, call_id: int) -> None:
    """Handle a Twilio media stream WebSocket connection.

    This endpoint receives audio from Twilio via a <Connect><Stream>,
    bridges it to the OpenAI Realtime API, and sends audio responses
    back to Twilio.

    Args:
        websocket: The incoming WebSocket connection from Twilio.
        call_id: The internal call ID for this conversation.
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for call %d", call_id)

    # Look up call and shop info
    call, shop = _get_call_and_shop(call_id)
    if not call or not shop:
        logger.error("Call %d or its shop not found, closing WebSocket", call_id)
        await websocket.close(code=1008, reason="Call not found")
        return

    shop_name = shop.name
    language = call.ai_agent_language or "en"

    # Create the voice agent
    agent = VoiceAgent(
        call_id=str(call_id),
        shop_name=shop_name,
        language=language,
    )

    try:
        # Connect to OpenAI Realtime API
        await agent.connect()
        logger.info("Voice agent connected to OpenAI for call %d", call_id)

        # Main message loop: receive from Twilio, forward to OpenAI
        while True:
            raw_message = await websocket.receive_text()
            data = json.loads(raw_message)

            # Process Twilio media stream message
            response_messages = await agent.handle_twilio_message(data)

            # Send any response messages back to Twilio
            for msg in response_messages:
                await websocket.send_text(json.dumps(msg))

    except WebSocketDisconnect:
        logger.info("Twilio WebSocket disconnected for call %d", call_id)
    except Exception as e:
        logger.error("Error in voice WebSocket for call %d: %s", call_id, e)
    finally:
        await agent.disconnect()
        logger.info("Voice agent cleaned up for call %d", call_id)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    db_status = "unknown"

    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        database=db_status,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
