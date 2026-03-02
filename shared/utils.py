"""Utility functions used across services."""

import re
import uuid
from datetime import datetime, time

from zoneinfo import ZoneInfo


def is_business_hours(shop: dict) -> bool:
    """Check if the current time is within the shop's business hours.

    Args:
        shop: Dict with 'timezone' (str) and 'business_hours' (dict) keys.
              business_hours format: {"monday": {"open": "08:00", "close": "18:00"}, ...}
    """
    tz = ZoneInfo(shop.get("timezone", "America/New_York"))
    now = datetime.now(tz)
    day_name = now.strftime("%A").lower()

    hours = shop.get("business_hours", {})
    day_hours = hours.get(day_name)
    if not day_hours:
        return False

    open_time = time.fromisoformat(day_hours["open"])
    close_time = time.fromisoformat(day_hours["close"])
    current_time = now.time()

    return open_time <= current_time <= close_time


def format_phone(phone: str) -> str:
    """Format a phone number to E.164 format (+1XXXXXXXXXX)."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    return f"+{digits}"


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())
