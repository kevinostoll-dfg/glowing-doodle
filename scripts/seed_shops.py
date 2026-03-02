"""Seed the database with sample shops, admin users, and phone numbers.

Creates three demo shops with associated admin users (each with a freshly
generated API key) and dedicated phone numbers.

Usage:
    python -m scripts.seed_shops
"""

from shared.auth import generate_api_key, hash_api_key
from shared.config import get_settings
from shared.database import SessionLocal
from shared.models.phone_number import PhoneNumber
from shared.models.shop import Shop
from shared.models.user import User

# Sample data for the three demo shops
SHOPS = [
    {
        "name": "Downtown Auto Care",
        "shop_code": "downtown-auto",
        "phone_number": "+15551000001",
        "timezone": "America/New_York",
        "address": "123 Main Street, New York, NY 10001",
        "admin_email": "admin@downtownauto.example.com",
        "numbers": [
            {"phone_number": "+15551000001", "number_type": "main", "lead_source": "website"},
            {"phone_number": "+15551000002", "number_type": "tracking", "lead_source": "google_ads"},
        ],
    },
    {
        "name": "Westside Mechanics",
        "shop_code": "westside-mech",
        "phone_number": "+15552000001",
        "timezone": "America/Chicago",
        "address": "456 West Avenue, Chicago, IL 60614",
        "admin_email": "admin@westsidemechanics.example.com",
        "numbers": [
            {"phone_number": "+15552000001", "number_type": "main", "lead_source": "website"},
            {"phone_number": "+15552000002", "number_type": "tracking", "lead_source": "yelp"},
        ],
    },
    {
        "name": "Harbor Auto Service",
        "shop_code": "harbor-auto",
        "phone_number": "+15553000001",
        "timezone": "America/Los_Angeles",
        "address": "789 Harbor Blvd, San Francisco, CA 94107",
        "admin_email": "admin@harborauto.example.com",
        "numbers": [
            {"phone_number": "+15553000001", "number_type": "main", "lead_source": "website"},
            {"phone_number": "+15553000002", "number_type": "toll-free", "lead_source": "radio"},
        ],
    },
]


def seed() -> None:
    """Insert sample shops, admin users, and phone numbers."""
    db = SessionLocal()
    api_keys: list[tuple[str, str, str]] = []  # (shop_name, email, raw_key)

    try:
        for shop_data in SHOPS:
            # Check whether the shop already exists
            existing = db.query(Shop).filter_by(shop_code=shop_data["shop_code"]).first()
            if existing:
                print(f"Shop '{shop_data['name']}' (code={shop_data['shop_code']}) already exists – skipping.")
                continue

            # Create shop
            shop = Shop(
                name=shop_data["name"],
                shop_code=shop_data["shop_code"],
                phone_number=shop_data["phone_number"],
                timezone=shop_data["timezone"],
                address=shop_data["address"],
                business_hours={
                    "monday": "08:00-18:00",
                    "tuesday": "08:00-18:00",
                    "wednesday": "08:00-18:00",
                    "thursday": "08:00-18:00",
                    "friday": "08:00-18:00",
                    "saturday": "09:00-14:00",
                    "sunday": "closed",
                },
            )
            db.add(shop)
            db.flush()  # populate shop.id

            # Create admin user with API key
            raw_key = generate_api_key()
            hashed_key = hash_api_key(raw_key)
            user = User(
                shop_id=shop.id,
                email=shop_data["admin_email"],
                api_key=hashed_key,
                role="admin",
            )
            db.add(user)

            api_keys.append((shop_data["name"], shop_data["admin_email"], raw_key))

            # Create phone numbers
            for num_data in shop_data["numbers"]:
                phone = PhoneNumber(
                    shop_id=shop.id,
                    phone_number=num_data["phone_number"],
                    number_type=num_data["number_type"],
                    lead_source=num_data["lead_source"],
                    is_active=True,
                )
                db.add(phone)

            print(f"Created shop '{shop_data['name']}' with admin user and phone numbers.")

        db.commit()

        # Print generated API keys to console
        if api_keys:
            print()
            print("=" * 72)
            print("  GENERATED API KEYS (store these securely – they cannot be recovered)")
            print("=" * 72)
            for shop_name, email, raw_key in api_keys:
                print(f"  Shop:  {shop_name}")
                print(f"  Email: {email}")
                print(f"  Key:   {raw_key}")
                print("-" * 72)
        else:
            print("\nNo new shops were created (all already existed).")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    """Entry point for seed_shops script."""
    settings = get_settings()
    print("Call Intelligence Platform – Seed Shops")
    print(f"Database: {settings.database_url}")
    print()
    seed()


if __name__ == "__main__":
    main()
