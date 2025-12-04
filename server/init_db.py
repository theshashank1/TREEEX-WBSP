"""
Database Initialization Script
Drops all existing tables and creates fresh ones.

Usage:
    python -m server.init_db
    python -m server.init_db --force  # Skip confirmation

WARNING: This will DELETE ALL DATA.  Use only for development/testing.
"""

import asyncio
import sys
from pathlib import Path

# Add server to path if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from server.core.config import settings
from server.models.access import User, Workspace, WorkspaceMember
from server.models.audit import WebhookLog

# Import Base and ALL models to register them with Base. metadata
from server.models.base import Base
from server.models.contacts import Contact, PhoneNumber
from server.models.marketing import Campaign, CampaignMessage, Template
from server.models.messaging import Conversation, MediaFile, Message


async def init_db(drop_all: bool = True):
    """Initialize database - drop all tables and create fresh ones"""

    if not settings.DATABASE_URL:
        print("❌ ERROR: DATABASE_URL is not set!")
        print("Please check your .env file and config. py")
        sys.exit(1)

    # Convert postgres:// to postgresql+asyncpg:// for async support
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"Database URL: {database_url[:50]}...")
    print()

    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        if drop_all:
            print("⚠️  WARNING: Dropping all existing tables...")
            print("-" * 60)

            # Drop all tables with CASCADE to handle foreign keys
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

            print("✅ All tables dropped successfully!")
            print()

        print("📦 Creating fresh tables...")
        print("-" * 60)

        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)

        print()
        print("✅ All tables created successfully!")

    await engine.dispose()

    print()
    print("=" * 60)
    print("DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)

    # List created tables
    print()
    print("📋 Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"   • {table_name}")
    print()
    print(f"Total: {len(Base. metadata.tables)} tables")


async def confirm_and_init():
    """Confirm before dropping tables"""

    print()
    print("⚠️  " + "=" * 56)
    print("⚠️  WARNING: THIS WILL DELETE ALL DATA IN THE DATABASE!")
    print("⚠️  " + "=" * 56)
    print()

    # Skip confirmation if --force flag is passed
    if "--force" in sys.argv or "-f" in sys.argv:
        print("Force flag detected.  Proceeding without confirmation...")
        await init_db(drop_all=True)
        return

    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()

    if response in ("yes", "y"):
        await init_db(drop_all=True)
    else:
        print("❌ Cancelled.  No changes were made.")


if __name__ == "__main__":
    asyncio.run(confirm_and_init())
