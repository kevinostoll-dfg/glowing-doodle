"""Initialize the database and run Alembic migrations.

Usage:
    python -m scripts.init_db
"""

import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from shared.config import get_settings


def _parse_db_url(database_url: str) -> tuple[str, str]:
    """Split a PostgreSQL URL into the server URL and the database name.

    Returns (server_url_with_default_db, target_db_name).
    """
    # Example: postgresql://user:pass@host:5432/calliq
    # We need to connect to 'postgres' db to create the target db
    parts = database_url.rsplit("/", 1)
    server_url = parts[0] + "/postgres"
    db_name = parts[1] if len(parts) > 1 else "calliq"
    # Strip query params from db_name if present
    if "?" in db_name:
        db_name = db_name.split("?")[0]
    return server_url, db_name


def ensure_database_exists() -> None:
    """Create the target database if it does not already exist."""
    from sqlalchemy import create_engine

    settings = get_settings()
    server_url, db_name = _parse_db_url(settings.database_url)

    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name},
            )
            if not result.scalar():
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Created database '{db_name}'.")
            else:
                print(f"Database '{db_name}' already exists.")
    except OperationalError as exc:
        print(f"Warning: could not connect to server to check/create database: {exc}")
        print("Make sure PostgreSQL is running and the connection details are correct.")
        sys.exit(1)
    except ProgrammingError as exc:
        print(f"Warning: could not create database: {exc}")
        sys.exit(1)
    finally:
        engine.dispose()


def run_migrations() -> None:
    """Run Alembic upgrade head."""
    print("Running Alembic migrations (upgrade head)...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Migration failed!")
        print(result.stderr)
        sys.exit(1)
    else:
        print(result.stdout)
        print("Migrations completed successfully.")


def main() -> None:
    """Create database (if needed) and apply all Alembic migrations."""
    print("=" * 60)
    print("Call Intelligence Platform – Database Initialization")
    print("=" * 60)

    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print()

    ensure_database_exists()
    run_migrations()

    print()
    print("Database is ready.")


if __name__ == "__main__":
    main()
