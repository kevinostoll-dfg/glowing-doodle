"""Deepgram integration for audio transcription."""

import logging
from dataclasses import dataclass, field

from deepgram import DeepgramClient, PrerecordedOptions

from shared.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """A single speaker utterance segment."""

    speaker: int
    text: str
    start: float
    end: float
    confidence: float = 0.0


@dataclass
class DeepgramResult:
    """Structured result from Deepgram transcription."""

    transcript: str
    speakers: list[dict] = field(default_factory=list)
    sentiment: str = "neutral"
    language: str = "en"
    utterances: list[SpeakerSegment] = field(default_factory=list)


async def transcribe_audio(audio_url: str) -> DeepgramResult:
    """Transcribe audio using Deepgram's PreRecorded API with nova-3 model.

    Args:
        audio_url: URL of the audio file to transcribe.

    Returns:
        DeepgramResult with transcript, speaker info, sentiment, and utterances.
    """
    settings = get_settings()
    client = DeepgramClient(settings.deepgram_api_key)

    options = PrerecordedOptions(
        model="nova-3",
        diarize=True,
        sentiment=True,
        language_detection=True,
        punctuate=True,
        utterances=True,
        smart_format=True,
    )

    logger.info("Sending audio to Deepgram for transcription: %s", audio_url)

    response = await client.listen.asyncrest.v("1").transcribe_url(
        {"url": audio_url},
        options,
    )

    return _parse_response(response)


def _parse_response(response) -> DeepgramResult:
    """Parse the Deepgram API response into a DeepgramResult.

    Args:
        response: The raw Deepgram API response object.

    Returns:
        Structured DeepgramResult.
    """
    result = response.results

    # Extract the full transcript from channels
    channels = result.channels
    transcript_parts = []
    for channel in channels:
        for alternative in channel.alternatives:
            transcript_parts.append(alternative.transcript)

    full_transcript = " ".join(transcript_parts)

    # Detect language from results
    detected_language = "en"
    if hasattr(result, "channels") and channels:
        first_channel = channels[0]
        if hasattr(first_channel, "detected_language"):
            detected_language = first_channel.detected_language or "en"

    # Parse diarization / utterances
    utterances = parse_diarization(response)

    # Aggregate speaker information
    speakers = _aggregate_speakers(utterances)

    # Determine overall sentiment from utterance-level sentiments
    sentiment = _extract_sentiment(response)

    return DeepgramResult(
        transcript=full_transcript,
        speakers=speakers,
        sentiment=sentiment,
        language=detected_language,
        utterances=utterances,
    )


def parse_diarization(response) -> list[SpeakerSegment]:
    """Extract speaker segments and utterances from Deepgram response.

    Args:
        response: The raw Deepgram API response object.

    Returns:
        List of SpeakerSegment objects representing diarized utterances.
    """
    segments: list[SpeakerSegment] = []

    # Deepgram returns utterances when utterances=True is set
    if hasattr(response.results, "utterances") and response.results.utterances:
        for utterance in response.results.utterances:
            segments.append(
                SpeakerSegment(
                    speaker=utterance.speaker,
                    text=utterance.transcript,
                    start=utterance.start,
                    end=utterance.end,
                    confidence=getattr(utterance, "confidence", 0.0),
                )
            )
    else:
        # Fall back to word-level diarization from channels
        for channel in response.results.channels:
            for alternative in channel.alternatives:
                if not hasattr(alternative, "words") or not alternative.words:
                    continue

                current_speaker = None
                current_text = []
                current_start = 0.0

                for word in alternative.words:
                    speaker = getattr(word, "speaker", 0)
                    if speaker != current_speaker:
                        if current_text and current_speaker is not None:
                            segments.append(
                                SpeakerSegment(
                                    speaker=current_speaker,
                                    text=" ".join(current_text),
                                    start=current_start,
                                    end=word.start,
                                    confidence=getattr(word, "confidence", 0.0),
                                )
                            )
                        current_speaker = speaker
                        current_text = [word.punctuated_word or word.word]
                        current_start = word.start
                    else:
                        current_text.append(word.punctuated_word or word.word)

                # Flush the last segment
                if current_text and current_speaker is not None:
                    last_word = alternative.words[-1]
                    segments.append(
                        SpeakerSegment(
                            speaker=current_speaker,
                            text=" ".join(current_text),
                            start=current_start,
                            end=last_word.end,
                            confidence=getattr(last_word, "confidence", 0.0),
                        )
                    )

    return segments


def _aggregate_speakers(utterances: list[SpeakerSegment]) -> list[dict]:
    """Aggregate utterance data by speaker.

    Args:
        utterances: List of SpeakerSegment objects.

    Returns:
        List of dicts with speaker label, total talk time, and utterance count.
    """
    speaker_data: dict[int, dict] = {}

    for seg in utterances:
        if seg.speaker not in speaker_data:
            speaker_data[seg.speaker] = {
                "speaker": seg.speaker,
                "label": f"Speaker {seg.speaker}",
                "total_talk_time": 0.0,
                "utterance_count": 0,
            }
        speaker_data[seg.speaker]["total_talk_time"] += seg.end - seg.start
        speaker_data[seg.speaker]["utterance_count"] += 1

    return list(speaker_data.values())


def _extract_sentiment(response) -> str:
    """Extract overall sentiment from Deepgram response.

    Args:
        response: The raw Deepgram API response.

    Returns:
        One of 'positive', 'neutral', or 'negative'.
    """
    try:
        sentiments = {"positive": 0, "neutral": 0, "negative": 0}
        for channel in response.results.channels:
            for alternative in channel.alternatives:
                if not hasattr(alternative, "words"):
                    continue
                for word in alternative.words:
                    if hasattr(word, "sentiment") and word.sentiment:
                        label = word.sentiment
                        if label in sentiments:
                            sentiments[label] += 1

        # Return the dominant sentiment, defaulting to neutral
        if not any(sentiments.values()):
            return "neutral"
        return max(sentiments, key=sentiments.get)
    except Exception:
        logger.debug("Could not extract sentiment from Deepgram response")
        return "neutral"
