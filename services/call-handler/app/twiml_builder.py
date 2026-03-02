"""TwiML response builders for various call scenarios."""


def build_forward_twiml(shop_phone: str, caller_id: str) -> str:
    """Build TwiML to forward (Dial) the call to the shop's phone number.

    Includes a timeout so the call falls through to voicemail if unanswered.

    Args:
        shop_phone: The shop's phone number to dial.
        caller_id: The caller ID to display (the Twilio number).

    Returns:
        TwiML XML string.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial timeout="25" callerId="{caller_id}" action="/status-callback" method="POST">
        <Number>{shop_phone}</Number>
    </Dial>
    <Say voice="Polly.Joanna">
        We're sorry, no one is available to take your call right now.
        Please leave a message after the beep.
    </Say>
    <Record maxLength="120" transcribe="true" action="/recording-callback" method="POST" />
</Response>"""


def build_ai_agent_twiml(call_id: str, ws_url: str) -> str:
    """Build TwiML to connect the call to the AI voice agent via WebSocket.

    Uses Twilio's <Connect><Stream> to bridge audio to the voice agent
    WebSocket endpoint.

    Args:
        call_id: The internal call ID for tracking.
        ws_url: The WebSocket URL of the voice agent service.

    Returns:
        TwiML XML string.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="call_id" value="{call_id}" />
        </Stream>
    </Connect>
</Response>"""


def build_voicemail_twiml() -> str:
    """Build TwiML for voicemail recording.

    Plays a generic message and records the caller's voicemail.

    Returns:
        TwiML XML string.
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Thank you for calling. We are unable to take your call right now.
        Please leave a message after the beep and we will get back to you
        as soon as possible.
    </Say>
    <Record maxLength="120" transcribe="true" action="/recording-callback" method="POST" />
    <Say voice="Polly.Joanna">We did not receive a recording. Goodbye.</Say>
</Response>"""


def build_greeting_twiml(shop_name: str) -> str:
    """Build TwiML for an interactive greeting with Gather for menu options.

    Greets the caller by shop name and presents menu choices.

    Args:
        shop_name: The name of the auto repair shop.

    Returns:
        TwiML XML string.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="/menu-selection" method="POST" timeout="5">
        <Say voice="Polly.Joanna">
            Thank you for calling {shop_name}.
            Press 1 to speak with a service advisor.
            Press 2 to check on the status of your vehicle.
            Press 3 to schedule an appointment.
            Or stay on the line to speak with our virtual assistant.
        </Say>
    </Gather>
    <Say voice="Polly.Joanna">
        We didn't receive your selection. Connecting you to our virtual assistant.
    </Say>
    <Redirect>/inbound</Redirect>
</Response>"""
