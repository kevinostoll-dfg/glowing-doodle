"""Storage client wrapper for downloading and uploading call recordings."""

import logging

import httpx

from shared.config import get_settings
from shared.storage import upload_recording as _upload_recording

logger = logging.getLogger(__name__)


async def download_recording(url: str) -> bytes:
    """Download a call recording from a URL.

    Args:
        url: The URL to download the recording from (e.g., Twilio recording URL).

    Returns:
        The raw audio bytes.

    Raises:
        httpx.HTTPStatusError: If the download fails with a non-2xx status.
    """
    logger.info("Downloading recording from: %s", url)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()

    logger.info(
        "Downloaded recording: %d bytes, content-type: %s",
        len(response.content),
        response.headers.get("content-type", "unknown"),
    )

    return response.content


def save_recording(call_id: int, audio_data: bytes) -> str:
    """Upload a call recording to S3-compatible storage.

    Args:
        call_id: The database ID of the call.
        audio_data: Raw audio file bytes.

    Returns:
        The S3 object key where the recording was stored.
    """
    settings = get_settings()
    key = f"recordings/{call_id}/audio.wav"

    logger.info(
        "Uploading recording for call %d to %s/%s",
        call_id,
        settings.s3_bucket,
        key,
    )

    return _upload_recording(audio_data, key)
