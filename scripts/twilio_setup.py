"""Configure Twilio phone numbers with webhook URLs.

This CLI tool updates Twilio phone numbers so that incoming voice calls
are routed to the Call Intelligence Platform webhook endpoints and status
callbacks are delivered for call lifecycle events.

Usage:
    # Configure a single phone number
    python -m scripts.twilio_setup \
        --phone-number +15551000001 \
        --base-url https://api.example.com

    # List all phone numbers on the account
    python -m scripts.twilio_setup --list

    # Configure all numbers on the account at once
    python -m scripts.twilio_setup \
        --all \
        --base-url https://api.example.com

    # Dry-run: show what would change without applying
    python -m scripts.twilio_setup \
        --phone-number +15551000001 \
        --base-url https://api.example.com \
        --dry-run
"""

import argparse
import sys

from twilio.rest import Client

from shared.config import get_settings


def get_twilio_client() -> Client:
    """Return an authenticated Twilio REST client."""
    settings = get_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        print("Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in the environment.")
        sys.exit(1)
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def list_numbers(client: Client) -> None:
    """Print all phone numbers on the Twilio account."""
    numbers = client.incoming_phone_numbers.list()
    if not numbers:
        print("No phone numbers found on this Twilio account.")
        return

    print(f"{'Phone Number':<20} {'Friendly Name':<30} {'Voice URL':<50}")
    print("-" * 100)
    for number in numbers:
        print(f"{number.phone_number:<20} {number.friendly_name:<30} {number.voice_url or '(not set)':<50}")


def configure_number(
    client: Client,
    phone_number: str,
    voice_url: str,
    status_callback: str,
    *,
    dry_run: bool = False,
) -> bool:
    """Update a single Twilio phone number with webhook URLs.

    Returns True if the number was found and updated (or would be in dry-run).
    """
    numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
    if not numbers:
        print(f"Error: phone number {phone_number} not found on this Twilio account.")
        return False

    incoming = numbers[0]

    if dry_run:
        print(f"[DRY RUN] Would update {phone_number} (SID: {incoming.sid}):")
        print(f"  voice_url          -> {voice_url}")
        print(f"  voice_method       -> POST")
        print(f"  status_callback    -> {status_callback}")
        print(f"  status_callback_method -> POST")
        return True

    incoming.update(
        voice_url=voice_url,
        voice_method="POST",
        status_callback=status_callback,
        status_callback_method="POST",
    )
    print(f"Updated {phone_number} (SID: {incoming.sid}):")
    print(f"  voice_url       = {voice_url}")
    print(f"  status_callback = {status_callback}")
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the Twilio setup CLI."""
    parser = argparse.ArgumentParser(
        description="Configure Twilio phone numbers with Call Intelligence Platform webhooks.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--phone-number",
        type=str,
        help="The E.164 phone number to configure (e.g. +15551000001).",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Configure all phone numbers on the Twilio account.",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List all phone numbers on the Twilio account and exit.",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL of the deployed API (e.g. https://api.example.com). "
        "Voice URL will be <base-url>/api/v1/twilio/voice and "
        "status callback will be <base-url>/api/v1/twilio/status.",
    )

    parser.add_argument(
        "--voice-path",
        type=str,
        default="/api/v1/twilio/voice",
        help="Path appended to --base-url for the voice webhook (default: /api/v1/twilio/voice).",
    )

    parser.add_argument(
        "--status-path",
        type=str,
        default="/api/v1/twilio/status",
        help="Path appended to --base-url for the status callback (default: /api/v1/twilio/status).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be changed without actually updating Twilio.",
    )

    return parser


def main() -> None:
    """Entry point for the Twilio setup CLI."""
    parser = build_parser()
    args = parser.parse_args()

    client = get_twilio_client()

    # Handle --list
    if args.list:
        list_numbers(client)
        return

    # For --phone-number and --all we require --base-url
    if not args.base_url:
        parser.error("--base-url is required when configuring phone numbers.")

    base_url = args.base_url.rstrip("/")
    voice_url = base_url + args.voice_path
    status_callback = base_url + args.status_path

    if args.phone_number:
        success = configure_number(
            client,
            args.phone_number,
            voice_url,
            status_callback,
            dry_run=args.dry_run,
        )
        if not success:
            sys.exit(1)

    elif args.all:
        numbers = client.incoming_phone_numbers.list()
        if not numbers:
            print("No phone numbers found on this Twilio account.")
            return

        print(f"Configuring {len(numbers)} phone number(s)...")
        print()
        failed = 0
        for number in numbers:
            ok = configure_number(
                client,
                number.phone_number,
                voice_url,
                status_callback,
                dry_run=args.dry_run,
            )
            if not ok:
                failed += 1
            print()

        if failed:
            print(f"Warning: {failed} number(s) could not be configured.")
            sys.exit(1)
        print("All numbers configured successfully.")

    else:
        parser.error("Specify --phone-number, --all, or --list.")


if __name__ == "__main__":
    main()
