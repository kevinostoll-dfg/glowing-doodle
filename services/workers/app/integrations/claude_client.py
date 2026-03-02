"""Anthropic Claude integration for call scoring and analysis."""

import json
import logging

import anthropic

from shared.config import get_settings

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


def score_call(
    transcript: str,
    rubric_criteria: list[dict],
    shop_name: str,
) -> dict:
    """Score a call transcript using the Anthropic Claude API.

    Sends a structured prompt requesting JSON-formatted scoring results,
    then parses and validates the response.

    Args:
        transcript: The full call transcript text.
        rubric_criteria: List of rubric category dicts, each containing
            name, description, weight, and criteria fields.
        shop_name: Name of the auto repair shop for context.

    Returns:
        Dict with keys: overall_score, category_scores, sentiment,
        intent, key_points, coaching_notes.

    Raises:
        ValueError: If the Claude response cannot be parsed as valid JSON
            or is missing required fields.
    """
    from app.prompts.scoring_rubric import get_scoring_prompt

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = get_scoring_prompt(transcript, rubric_criteria, shop_name)

    logger.info("Sending call transcript to Claude for analysis (shop: %s)", shop_name)

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    # Extract text content from response
    response_text = ""
    for block in message.content:
        if block.type == "text":
            response_text += block.text

    logger.debug("Claude raw response: %s", response_text[:500])

    return _parse_and_validate_response(response_text)


def _parse_and_validate_response(response_text: str) -> dict:
    """Parse and validate the JSON response from Claude.

    Handles cases where Claude wraps JSON in markdown code blocks.

    Args:
        response_text: Raw text response from the Claude API.

    Returns:
        Validated dict with scoring results.

    Raises:
        ValueError: If parsing fails or required fields are missing.
    """
    # Strip markdown code block wrappers if present
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Claude response as JSON: %s", exc)
        raise ValueError(f"Claude response is not valid JSON: {exc}") from exc

    # Validate required fields
    required_fields = [
        "overall_score",
        "category_scores",
        "sentiment",
        "intent",
        "key_points",
        "coaching_notes",
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Claude response missing required fields: {missing}")

    # Validate and clamp overall_score
    score = data["overall_score"]
    if not isinstance(score, (int, float)):
        raise ValueError(f"overall_score must be a number, got {type(score).__name__}")
    data["overall_score"] = max(0.0, min(100.0, float(score)))

    # Validate category_scores structure
    if not isinstance(data["category_scores"], list):
        raise ValueError("category_scores must be a list")
    for cat in data["category_scores"]:
        if not isinstance(cat, dict):
            raise ValueError("Each category_score must be a dict")
        if "name" not in cat or "score" not in cat:
            raise ValueError("Each category_score must have 'name' and 'score'")
        cat["score"] = max(0.0, min(100.0, float(cat["score"])))

    # Validate sentiment
    valid_sentiments = {"positive", "neutral", "negative"}
    if data["sentiment"] not in valid_sentiments:
        logger.warning(
            "Unexpected sentiment value '%s', defaulting to 'neutral'",
            data["sentiment"],
        )
        data["sentiment"] = "neutral"

    # Validate key_points is a list
    if not isinstance(data["key_points"], list):
        data["key_points"] = [str(data["key_points"])]

    # Ensure coaching_notes is a string
    if not isinstance(data["coaching_notes"], str):
        data["coaching_notes"] = str(data["coaching_notes"])

    return data
