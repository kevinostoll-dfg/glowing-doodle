"""Tool definitions and execution for the AI voice agent.

These tools are exposed to OpenAI's Realtime API as callable functions
that the AI agent can invoke during a conversation.
"""

import logging
from datetime import datetime

from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.call import Call
from shared.models.shop import Shop

logger = logging.getLogger(__name__)
settings = get_settings()

# OpenAI function definitions for the Realtime API session configuration
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "save_message",
        "description": (
            "Save a message from the caller for the shop team. Use this when "
            "the caller wants to leave a message, report a vehicle issue, or "
            "provide information for the shop."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "caller_name": {
                    "type": "string",
                    "description": "The name of the caller.",
                },
                "caller_phone": {
                    "type": "string",
                    "description": "The caller's phone number for callbacks.",
                },
                "message": {
                    "type": "string",
                    "description": "The message content from the caller.",
                },
                "vehicle_info": {
                    "type": "string",
                    "description": (
                        "Vehicle details if mentioned (make, model, year)."
                    ),
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "How urgent the caller's request seems.",
                },
            },
            "required": ["caller_name", "message"],
        },
    },
    {
        "type": "function",
        "name": "schedule_callback",
        "description": (
            "Schedule a callback request so the shop can return the caller's "
            "call. Use when the caller wants to be called back."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "caller_name": {
                    "type": "string",
                    "description": "The name of the caller.",
                },
                "caller_phone": {
                    "type": "string",
                    "description": "The phone number to call back.",
                },
                "preferred_time": {
                    "type": "string",
                    "description": (
                        "When the caller prefers to be called back "
                        "(e.g., 'morning', 'afternoon', 'anytime')."
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": "Brief reason for the callback.",
                },
            },
            "required": ["caller_name", "caller_phone"],
        },
    },
    {
        "type": "function",
        "name": "get_shop_hours",
        "description": (
            "Get the shop's business hours. Use when the caller asks about "
            "when the shop is open or what the operating hours are."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "transfer_to_human",
        "description": (
            "Transfer the call to a human staff member. Use when the caller "
            "explicitly asks to speak with a person, or when the request is "
            "beyond what you can handle."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the caller wants to be transferred.",
                },
            },
            "required": [],
        },
    },
]


async def execute_tool(tool_name: str, arguments: dict, call_id: str) -> dict:
    """Dispatch and execute a tool call from the AI agent.

    Args:
        tool_name: The name of the tool to execute.
        arguments: The arguments passed by the AI agent.
        call_id: The internal call ID for context.

    Returns:
        A dict with the tool execution result.
    """
    logger.info("Executing tool '%s' for call %s", tool_name, call_id)

    if tool_name == "save_message":
        return await _save_message(arguments, call_id)
    elif tool_name == "schedule_callback":
        return await _schedule_callback(arguments, call_id)
    elif tool_name == "get_shop_hours":
        return await _get_shop_hours(call_id)
    elif tool_name == "transfer_to_human":
        return await _transfer_to_human(arguments, call_id)
    else:
        logger.warning("Unknown tool '%s' called on call %s", tool_name, call_id)
        return {"success": False, "error": f"Unknown tool: {tool_name}"}


async def _save_message(arguments: dict, call_id: str) -> dict:
    """Save a caller's message to the call record.

    Stores the message details in the call's key_points JSONB field
    so the shop team can review it later.
    """
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == int(call_id)).first()
        if not call:
            return {"success": False, "error": "Call not found"}

        message_data = {
            "type": "voicemail_message",
            "caller_name": arguments.get("caller_name", "Unknown"),
            "caller_phone": arguments.get("caller_phone", ""),
            "message": arguments.get("message", ""),
            "vehicle_info": arguments.get("vehicle_info", ""),
            "urgency": arguments.get("urgency", "medium"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Append to key_points
        existing_points = call.key_points or []
        existing_points.append(message_data)
        call.key_points = existing_points

        # Update caller name if we have it
        if arguments.get("caller_name"):
            call.caller_name = arguments["caller_name"]

        db.commit()
        logger.info("Message saved for call %s from %s", call_id, arguments.get("caller_name"))

        return {
            "success": True,
            "message": "Message has been saved. The shop team will receive it.",
        }
    except Exception as e:
        logger.error("Failed to save message for call %s: %s", call_id, e)
        db.rollback()
        return {"success": False, "error": "Failed to save message"}
    finally:
        db.close()


async def _schedule_callback(arguments: dict, call_id: str) -> dict:
    """Schedule a callback request for the shop team.

    Stores the callback details in the call's key_points JSONB field.
    """
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == int(call_id)).first()
        if not call:
            return {"success": False, "error": "Call not found"}

        callback_data = {
            "type": "callback_request",
            "caller_name": arguments.get("caller_name", "Unknown"),
            "caller_phone": arguments.get("caller_phone", ""),
            "preferred_time": arguments.get("preferred_time", "anytime"),
            "reason": arguments.get("reason", ""),
            "timestamp": datetime.utcnow().isoformat(),
        }

        existing_points = call.key_points or []
        existing_points.append(callback_data)
        call.key_points = existing_points

        if arguments.get("caller_name"):
            call.caller_name = arguments["caller_name"]

        db.commit()
        logger.info(
            "Callback scheduled for call %s: %s at %s",
            call_id,
            arguments.get("caller_phone"),
            arguments.get("preferred_time"),
        )

        return {
            "success": True,
            "message": (
                f"Callback has been scheduled. The shop will call "
                f"{arguments.get('caller_name', 'you')} back at "
                f"{arguments.get('caller_phone', 'the number on file')} "
                f"{arguments.get('preferred_time', 'as soon as possible')}."
            ),
        }
    except Exception as e:
        logger.error("Failed to schedule callback for call %s: %s", call_id, e)
        db.rollback()
        return {"success": False, "error": "Failed to schedule callback"}
    finally:
        db.close()


async def _get_shop_hours(call_id: str) -> dict:
    """Retrieve the shop's business hours for the AI to relay to the caller."""
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == int(call_id)).first()
        if not call:
            return {"success": False, "error": "Call not found"}

        shop = db.query(Shop).filter(Shop.id == call.shop_id).first()
        if not shop:
            return {"success": False, "error": "Shop not found"}

        business_hours = shop.business_hours or {}

        # Format hours into a human-readable structure
        formatted_hours = {}
        day_order = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]
        for day in day_order:
            hours = business_hours.get(day)
            if hours:
                formatted_hours[day] = f"{hours.get('open', 'N/A')} - {hours.get('close', 'N/A')}"
            else:
                formatted_hours[day] = "Closed"

        return {
            "success": True,
            "shop_name": shop.name,
            "timezone": shop.timezone,
            "hours": formatted_hours,
        }
    except Exception as e:
        logger.error("Failed to get shop hours for call %s: %s", call_id, e)
        return {"success": False, "error": "Failed to retrieve shop hours"}
    finally:
        db.close()


async def _transfer_to_human(arguments: dict, call_id: str) -> dict:
    """Attempt to transfer the caller to a human staff member.

    In practice, this signals the call handler to initiate a transfer.
    For now, it records the transfer request and informs the caller.
    """
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == int(call_id)).first()
        if not call:
            return {"success": False, "error": "Call not found"}

        shop = db.query(Shop).filter(Shop.id == call.shop_id).first()
        if not shop or not shop.phone_number:
            return {
                "success": False,
                "message": (
                    "I'm sorry, there's no one available to transfer you to "
                    "right now. Would you like to leave a message or schedule "
                    "a callback instead?"
                ),
            }

        transfer_data = {
            "type": "transfer_request",
            "reason": arguments.get("reason", "Caller requested transfer"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        existing_points = call.key_points or []
        existing_points.append(transfer_data)
        call.key_points = existing_points
        db.commit()

        logger.info("Transfer requested for call %s to shop %s", call_id, shop.name)

        return {
            "success": True,
            "message": (
                "I'll transfer you now. Please hold while I connect you "
                "to a team member."
            ),
            "transfer_number": shop.phone_number,
        }
    except Exception as e:
        logger.error("Failed to process transfer for call %s: %s", call_id, e)
        db.rollback()
        return {"success": False, "error": "Failed to process transfer"}
    finally:
        db.close()
