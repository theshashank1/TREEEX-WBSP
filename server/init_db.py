"""
Database Initialization Script - server/init_db.py

Drops all existing tables and creates fresh ones.
WARNING: This will DELETE ALL DATA. Use only for development/testing.

Usage:
    python -m server.init_db [--force]
"""

import asyncio
import sys
from pathlib import Path

# Add server to path if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from server.core.config import settings

# Import Base and ALL models to register them with Base.metadata
from server.models.access import User, Workspace, WorkspaceMember  # noqa
from server.models.audit import WebhookLog  # noqa
from server.models.base import Base
from server.models.contacts import Channel, Contact, ContactChannelState  # noqa
from server.models.marketing import Campaign, CampaignMessage, Template  # noqa
from server.models.messaging import Conversation, MediaFile, Message  # noqa


async def init_db(drop_all: bool = True):
    """Initialize database - drop all tables and create fresh ones."""

    if not settings.DATABASE_URL:
        print("❌ ERROR: DATABASE_URL is not set!")
        sys.exit(1)

    # Convert postgres:// to postgresql+asyncpg:// for async support
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print(f"Database URL: {database_url[:50]}...")
    print("=" * 60)

    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        if drop_all:
            print("⚠️  Dropping all existing tables...")

            # Drop all tables with CASCADE to handle foreign keys
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

            print("✅ All tables dropped successfully!\n")

        print("📦 Creating fresh tables...")

        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)

        print("✅ All tables created successfully!")

    await engine.dispose()

    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)

    # List created tables
    print("\n📋 Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"   • {table_name}")
    print(f"\nTotal: {len(Base.metadata.tables)} tables")


async def confirm_and_init():
    """Confirm before dropping tables."""
    print("\n⚠️  " + "=" * 56)
    print("⚠️  WARNING: THIS WILL DELETE ALL DATA IN THE DATABASE!")
    print("⚠️  " + "=" * 56 + "\n")

    # Skip confirmation if --force flag is passed
    if "--force" in sys.argv or "-f" in sys.argv:
        print("Force flag detected. Proceeding without confirmation...")
        await init_db(drop_all=True)
        return

    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()

    if response in ("yes", "y"):
        await init_db(drop_all=True)
    else:
        print("❌ Cancelled. No changes were made.")


if __name__ == "__main__":
    asyncio.run(confirm_and_init())
