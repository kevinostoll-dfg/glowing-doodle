"""VoiceAgent - bridges Twilio media streams with OpenAI Realtime API."""

import asyncio
import base64
import json
import logging

import websockets

from app.audio import build_mark_message, build_media_message
from app.scripts import get_system_prompt
from app.tools import TOOL_DEFINITIONS, execute_tool
from shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
OPENAI_MODEL = "gpt-4o-realtime-preview"


class VoiceAgent:
    """AI voice agent that bridges Twilio and OpenAI Realtime API.

    Manages bidirectional audio streaming between a Twilio media stream
    (mulaw 8kHz) and OpenAI's Realtime API, handling function calls
    and conversation state.

    Args:
        call_id: The internal call ID for tracking.
        shop_name: The name of the auto repair shop for personalization.
        language: The language for the conversation ('en' or 'es').
    """

    def __init__(self, call_id: str, shop_name: str, language: str = "en") -> None:
        self.call_id = call_id
        self.shop_name = shop_name
        self.language = language
        self.stream_sid: str | None = None
        self.openai_ws: websockets.WebSocketClientProtocol | None = None
        self._openai_listener_task: asyncio.Task | None = None
        self._twilio_response_queue: asyncio.Queue = asyncio.Queue()
        self._connected = False

    async def connect(self) -> None:
        """Establish WebSocket connection to OpenAI Realtime API.

        Sends the session configuration including the system prompt,
        voice settings, and tool definitions.
        """
        url = f"{OPENAI_REALTIME_URL}?model={OPENAI_MODEL}"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        self.openai_ws = await websockets.connect(url, additional_headers=headers)
        self._connected = True

        # Configure the session
        system_prompt = get_system_prompt(self.language, self.shop_name)
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": system_prompt,
                "voice": "alloy",
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {
                    "model": "whisper-1",
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "tools": TOOL_DEFINITIONS,
            },
        }
        await self.openai_ws.send(json.dumps(session_config))
        logger.info("Session configured for call %s", self.call_id)

        # Start background listener for OpenAI messages
        self._openai_listener_task = asyncio.create_task(self._listen_openai())

    async def disconnect(self) -> None:
        """Close the OpenAI WebSocket connection and clean up."""
        self._connected = False

        if self._openai_listener_task and not self._openai_listener_task.done():
            self._openai_listener_task.cancel()
            try:
                await self._openai_listener_task
            except asyncio.CancelledError:
                pass

        if self.openai_ws:
            try:
                await self.openai_ws.close()
            except Exception:
                pass
            self.openai_ws = None

        logger.info("Voice agent disconnected for call %s", self.call_id)

    async def handle_twilio_message(self, data: dict) -> list[dict]:
        """Process an incoming Twilio media stream message.

        Handles the following Twilio stream events:
        - connected: Stream connection established
        - start: Stream started, captures stream SID
        - media: Audio data, forwarded to OpenAI
        - stop: Stream ended

        Args:
            data: The parsed JSON message from Twilio.

        Returns:
            A list of response messages to send back to Twilio.
        """
        event = data.get("event")
        responses: list[dict] = []

        if event == "connected":
            logger.info("Twilio stream connected for call %s", self.call_id)

        elif event == "start":
            self.stream_sid = data.get("start", {}).get("streamSid")
            logger.info(
                "Twilio stream started: %s for call %s",
                self.stream_sid,
                self.call_id,
            )

        elif event == "media":
            # Forward audio from Twilio to OpenAI
            payload = data.get("media", {}).get("payload", "")
            if self.openai_ws and self._connected:
                audio_append = {
                    "type": "input_audio_buffer.append",
                    "audio": payload,
                }
                try:
                    await self.openai_ws.send(json.dumps(audio_append))
                except Exception as e:
                    logger.error("Error sending audio to OpenAI: %s", e)

        elif event == "stop":
            logger.info("Twilio stream stopped for call %s", self.call_id)

        # Drain any queued response messages from the OpenAI listener
        while not self._twilio_response_queue.empty():
            try:
                msg = self._twilio_response_queue.get_nowait()
                responses.append(msg)
            except asyncio.QueueEmpty:
                break

        return responses

    async def _listen_openai(self) -> None:
        """Background task that listens for messages from OpenAI Realtime API.

        Processes various OpenAI event types and queues audio responses
        for sending back to Twilio.
        """
        if not self.openai_ws:
            return

        try:
            async for raw_message in self.openai_ws:
                if not self._connected:
                    break

                data = json.loads(raw_message)
                await self.handle_openai_message(data)

        except websockets.exceptions.ConnectionClosed:
            logger.info("OpenAI WebSocket closed for call %s", self.call_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Error in OpenAI listener for call %s: %s", self.call_id, e)

    async def handle_openai_message(self, data: dict) -> None:
        """Process a message from the OpenAI Realtime API.

        Handles audio deltas (streamed back to Twilio), function calls,
        and other conversation events.

        Args:
            data: The parsed JSON message from OpenAI.
        """
        event_type = data.get("type", "")

        if event_type == "session.created":
            logger.info("OpenAI session created for call %s", self.call_id)

        elif event_type == "session.updated":
            logger.info("OpenAI session updated for call %s", self.call_id)

        elif event_type == "response.audio.delta":
            # Stream audio back to Twilio
            audio_delta = data.get("delta", "")
            if self.stream_sid and audio_delta:
                media_msg = build_media_message(self.stream_sid, audio_delta)
                await self._twilio_response_queue.put(media_msg)

        elif event_type == "response.audio.done":
            # Mark the end of an audio segment
            if self.stream_sid:
                mark_msg = build_mark_message(self.stream_sid, "audio_done")
                await self._twilio_response_queue.put(mark_msg)

        elif event_type == "response.function_call_arguments.done":
            # Handle function calls from OpenAI
            await self._handle_function_call(data)

        elif event_type == "input_audio_buffer.speech_started":
            logger.debug("User started speaking on call %s", self.call_id)

        elif event_type == "input_audio_buffer.speech_stopped":
            logger.debug("User stopped speaking on call %s", self.call_id)

        elif event_type == "response.done":
            logger.debug("OpenAI response completed for call %s", self.call_id)

        elif event_type == "error":
            error_info = data.get("error", {})
            logger.error(
                "OpenAI error for call %s: %s", self.call_id, error_info
            )

    async def _handle_function_call(self, data: dict) -> None:
        """Execute a function call requested by OpenAI and return the result.

        Args:
            data: The function_call_arguments.done event from OpenAI.
        """
        call_id_field = data.get("call_id", "")
        function_name = data.get("name", "")
        arguments_str = data.get("arguments", "{}")

        logger.info(
            "Function call on call %s: %s(%s)",
            self.call_id,
            function_name,
            arguments_str,
        )

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        # Execute the tool
        result = await execute_tool(function_name, arguments, self.call_id)

        # Send the function result back to OpenAI
        if self.openai_ws and self._connected:
            function_output = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id_field,
                    "output": json.dumps(result),
                },
            }
            await self.openai_ws.send(json.dumps(function_output))

            # Request OpenAI to generate a response based on the function output
            response_create = {"type": "response.create"}
            await self.openai_ws.send(json.dumps(response_create))
