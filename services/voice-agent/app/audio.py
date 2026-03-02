"""Audio encoding/decoding utilities for Twilio media streams.

Handles conversion between PCM linear audio and G.711 mu-law encoding,
and builds Twilio media stream message payloads.
"""

import audioop
import base64
import json


def encode_mulaw(pcm_data: bytes) -> bytes:
    """Encode PCM linear 16-bit audio to G.711 mu-law.

    Twilio media streams use mu-law encoding at 8kHz sample rate.
    This converts raw PCM (16-bit, 8kHz) to mu-law for sending
    audio back to Twilio.

    Args:
        pcm_data: Raw PCM audio bytes (16-bit signed, 8kHz).

    Returns:
        Mu-law encoded audio bytes.
    """
    return audioop.lin2ulaw(pcm_data, 2)


def decode_mulaw(mulaw_data: bytes) -> bytes:
    """Decode G.711 mu-law audio to PCM linear 16-bit.

    Converts mu-law encoded audio from Twilio into raw PCM
    (16-bit signed, 8kHz) for processing or forwarding to
    speech-to-text services.

    Args:
        mulaw_data: Mu-law encoded audio bytes.

    Returns:
        Raw PCM audio bytes (16-bit signed, 8kHz).
    """
    return audioop.ulaw2lin(mulaw_data, 2)


def build_media_message(stream_sid: str, payload: str) -> dict:
    """Create a Twilio media stream message for sending audio.

    Builds the JSON structure that Twilio expects when sending
    audio data back through a media stream WebSocket.

    Args:
        stream_sid: The Twilio stream SID identifying the active stream.
        payload: Base64-encoded audio data (mu-law format).

    Returns:
        Dict representing the Twilio media message, ready for JSON serialization.
    """
    return {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": payload,
        },
    }


def build_mark_message(stream_sid: str, name: str) -> dict:
    """Create a Twilio mark message for synchronization.

    Mark messages are used to track when Twilio has finished playing
    audio. When the audio preceding a mark has been played, Twilio
    sends a 'mark' event back on the WebSocket.

    Args:
        stream_sid: The Twilio stream SID identifying the active stream.
        name: A label for this mark point (e.g., 'audio_done', 'utterance_end').

    Returns:
        Dict representing the Twilio mark message, ready for JSON serialization.
    """
    return {
        "event": "mark",
        "streamSid": stream_sid,
        "mark": {
            "name": name,
        },
    }
