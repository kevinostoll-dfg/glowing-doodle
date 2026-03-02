"""Scoring rubric and prompt templates for call analysis."""

DEFAULT_RUBRIC: list[dict] = [
    {
        "name": "Greeting & Professionalism",
        "description": "How well the advisor greeted the caller, identified themselves and the shop.",
        "weight": 0.15,
        "criteria": [
            "Answered within 3 rings",
            "Identified self and shop name",
            "Used a warm, professional tone",
            "Asked how they can help",
        ],
    },
    {
        "name": "Needs Discovery",
        "description": "How effectively the advisor identified the caller's needs and vehicle issues.",
        "weight": 0.20,
        "criteria": [
            "Asked clarifying questions about the vehicle problem",
            "Confirmed vehicle year, make, and model",
            "Gathered relevant symptom details",
            "Listened actively without interrupting",
        ],
    },
    {
        "name": "Service Knowledge",
        "description": "Demonstration of technical knowledge and ability to explain services clearly.",
        "weight": 0.15,
        "criteria": [
            "Explained the likely issue in understandable terms",
            "Described the recommended service or repair",
            "Provided a rough timeline for the work",
            "Addressed safety concerns if applicable",
        ],
    },
    {
        "name": "Pricing & Transparency",
        "description": "How clearly pricing, estimates, and potential costs were communicated.",
        "weight": 0.15,
        "criteria": [
            "Provided a price estimate or range",
            "Explained what the estimate includes",
            "Mentioned diagnostic fees if applicable",
            "Was upfront about potential additional costs",
        ],
    },
    {
        "name": "Appointment Booking",
        "description": "Effectiveness in converting the call into a booked appointment.",
        "weight": 0.20,
        "criteria": [
            "Offered specific appointment times",
            "Created urgency when appropriate",
            "Confirmed appointment details",
            "Collected customer contact information",
        ],
    },
    {
        "name": "Closing & Follow-Up",
        "description": "How well the advisor closed the call and set expectations.",
        "weight": 0.15,
        "criteria": [
            "Summarized next steps clearly",
            "Thanked the caller",
            "Offered additional help before hanging up",
            "Mentioned any follow-up actions",
        ],
    },
]


def get_scoring_prompt(transcript: str, criteria: list[dict], shop_name: str) -> str:
    """Build the full Claude prompt for call scoring.

    Args:
        transcript: The full call transcript text.
        criteria: List of rubric category dicts, each with name, description,
                  weight, and criteria fields.
        shop_name: The name of the auto repair shop for context.

    Returns:
        A formatted prompt string ready to send to the Claude API.
    """
    rubric_sections = []
    for category in criteria:
        criteria_bullets = "\n".join(
            f"      - {c}" for c in category.get("criteria", [])
        )
        rubric_sections.append(
            f"  - **{category['name']}** (weight: {category['weight']:.0%})\n"
            f"    Description: {category['description']}\n"
            f"    Criteria:\n{criteria_bullets}"
        )

    rubric_text = "\n\n".join(rubric_sections)

    return f"""You are an expert call quality analyst for auto repair shops. Your job is to analyze phone call transcripts and score service advisor performance.

## Context
Shop Name: {shop_name}
This is a phone call transcript from the shop's service line.

## Scoring Rubric

{rubric_text}

## Transcript

{transcript}

## Instructions

Analyze the transcript above against each rubric category. For each category:
1. Score from 0 to 100 based on how well the criteria were met.
2. Provide a brief justification for the score.

Then provide:
- An overall weighted score (0-100) calculated from the category scores and their weights.
- The overall sentiment of the caller (positive, neutral, or negative).
- The caller's primary intent (e.g., "schedule oil change", "get brake repair quote", "complaint about service", "general inquiry").
- A list of 3-5 key points from the call.
- Coaching notes for the service advisor with specific, actionable improvement suggestions.

## Required Output Format

Respond ONLY with valid JSON in the following structure:

{{
  "overall_score": <float 0-100>,
  "category_scores": [
    {{
      "name": "<category name>",
      "score": <float 0-100>,
      "justification": "<brief reason>"
    }}
  ],
  "sentiment": "<positive|neutral|negative>",
  "intent": "<caller's primary intent>",
  "key_points": [
    "<key point 1>",
    "<key point 2>",
    "<key point 3>"
  ],
  "coaching_notes": "<specific coaching feedback for the advisor>"
}}"""
