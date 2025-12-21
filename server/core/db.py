"""
Async Database Configuration - server/core/db.py

Configures SQLAlchemy asynchronous engine and session maker with SSL support.
"""

import ssl
import sys
from urllib.parse import parse_qs, urlencode, urlparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.core.config import settings


def create_db_engine_and_session_factory():
    """Create async engine and session factory, handling SSL for asyncpg."""
    if not settings.DATABASE_URL:
        # Critical error if DB is missing
        print("❌ ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        raise ValueError("DATABASE_URL not configured")

    url_str = str(settings.DATABASE_URL)
    parsed_url = urlparse(url_str)

    # Ensure correct async scheme
    scheme = parsed_url.scheme
    if scheme == "postgresql":
        scheme = "postgresql+asyncpg"

    query_params = parse_qs(parsed_url.query)

    # Extract sslmode before creating async URL
    ssl_mode = query_params.get("sslmode", [None])[0]

    # Remove sslmode from query params (asyncpg doesn't accept it in URL)
    if "sslmode" in query_params:
        del query_params["sslmode"]

    new_query = urlencode(query_params, doseq=True)

    async_url = parsed_url._replace(
        scheme=scheme,
        query=new_query,
    ).geturl()

    connect_args = {}

    # Configure SSL for asyncpg via connect_args
    if ssl_mode and ssl_mode != "disable":
        if ssl_mode in ("require", "prefer", "allow"):
            connect_args["ssl"] = True
        elif ssl_mode in ("verify-ca", "verify-full"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = ssl_mode == "verify-full"
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            connect_args["ssl"] = ssl_context

    engine = create_async_engine(
        async_url,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    return engine, session_factory


# Create global engine and session maker
try:
    engine, async_session_maker = create_db_engine_and_session_factory()
except ValueError:
    # Allow import to succeed (e.g. for tests)
    engine = None
    async_session_maker = None


async def get_async_session():
    """Dependency for FastAPI routes to get a database session."""
    if async_session_maker is None:
        raise RuntimeError("Database is not configured. Cannot create session.")

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
