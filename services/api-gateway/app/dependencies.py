"""Shared FastAPI dependencies for the API Gateway."""

from fastapi import Depends, Header, HTTPException, Request, status
from twilio.request_validator import RequestValidator

from shared.auth import get_current_user  # noqa: F401 – re-exported
from shared.config import get_settings
from shared.database import get_db  # noqa: F401 – re-exported


def validate_twilio_signature(
    request: Request,
    x_twilio_signature: str = Header(..., alias="X-Twilio-Signature"),
):
    """FastAPI dependency that validates the incoming Twilio webhook signature.

    Raises 403 if the signature is invalid.
    """
    settings = get_settings()

    if not settings.twilio_auth_token:
        # When no auth token is configured (e.g. local development) skip validation.
        return

    validator = RequestValidator(settings.twilio_auth_token)

    # Reconstruct the full URL the request was sent to.
    url = str(request.url)

    # Twilio sends form-encoded POST bodies; we need the parsed params.
    # Because this dependency is synchronous we cannot use `await request.form()`.
    # Instead we rely on the body being read by FastAPI before this dependency
    # executes (which is the case for Form-data endpoints).
    # For synchronous access we fall back to an empty dict and let the
    # validator compare against URL params only, which is how Twilio signs
    # GET requests. For POST, the router function should use
    # `validate_twilio_post` instead (see below).
    params: dict[str, str] = dict(request.query_params)

    if not validator.validate(url, params, x_twilio_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )


async def validate_twilio_post(request: Request):
    """Async dependency for Twilio POST webhooks that reads the form body.

    Must be used for POST endpoints that receive form-encoded data from Twilio.
    """
    settings = get_settings()

    if not settings.twilio_auth_token:
        return

    validator = RequestValidator(settings.twilio_auth_token)
    url = str(request.url)

    form_data = await request.form()
    params = {k: v for k, v in form_data.items() if isinstance(v, str)}

    signature = request.headers.get("X-Twilio-Signature", "")
    if not validator.validate(url, params, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )
