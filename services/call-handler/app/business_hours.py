"""Business hours checking with timezone awareness."""

import logging
from datetime import datetime, time

from zoneinfo import ZoneInfo

from shared.models.shop import Shop

logger = logging.getLogger(__name__)


def check_business_hours(shop: Shop) -> bool:
    """Check if the shop is currently within business hours.

    Uses the shop's timezone and JSONB business_hours configuration
    to determine if the shop is open right now.

    The business_hours field is expected to be a dict like:
        {
            "monday": {"open": "08:00", "close": "18:00"},
            "tuesday": {"open": "08:00", "close": "18:00"},
            ...
        }

    Days without entries are treated as closed.

    Args:
        shop: The Shop ORM model instance.

    Returns:
        True if the shop is currently open, False otherwise.
    """
    timezone_str = shop.timezone or "America/New_York"
    business_hours = shop.business_hours or {}

    try:
        tz = ZoneInfo(timezone_str)
    except (KeyError, ValueError):
        logger.warning(
            "Invalid timezone '%s' for shop %d, defaulting to America/New_York",
            timezone_str,
            shop.id,
        )
        tz = ZoneInfo("America/New_York")

    now = datetime.now(tz)
    day_name = now.strftime("%A").lower()

    day_hours = business_hours.get(day_name)
    if not day_hours:
        logger.debug("Shop %d is closed on %s", shop.id, day_name)
        return False

    try:
        open_time = time.fromisoformat(day_hours["open"])
        close_time = time.fromisoformat(day_hours["close"])
    except (KeyError, ValueError) as e:
        logger.warning(
            "Invalid business hours format for shop %d on %s: %s",
            shop.id,
            day_name,
            e,
        )
        return False

    current_time = now.time()
    is_open = open_time <= current_time <= close_time

    logger.debug(
        "Shop %d on %s: open=%s close=%s current=%s is_open=%s",
        shop.id,
        day_name,
        open_time,
        close_time,
        current_time,
        is_open,
    )

    return is_open


def get_current_day_hours(shop: Shop) -> dict | None:
    """Get today's open/close times for the shop.

    Args:
        shop: The Shop ORM model instance.

    Returns:
        Dict with 'open' and 'close' keys (time strings), or None if closed today.
    """
    timezone_str = shop.timezone or "America/New_York"
    business_hours = shop.business_hours or {}

    try:
        tz = ZoneInfo(timezone_str)
    except (KeyError, ValueError):
        tz = ZoneInfo("America/New_York")

    now = datetime.now(tz)
    day_name = now.strftime("%A").lower()

    day_hours = business_hours.get(day_name)
    if not day_hours:
        return None

    return {
        "day": day_name,
        "open": day_hours.get("open"),
        "close": day_hours.get("close"),
        "timezone": timezone_str,
    }
