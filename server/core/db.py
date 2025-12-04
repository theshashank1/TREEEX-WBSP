"""
Async Database Configuration for asyncpg
"""

import ssl
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.core.config import settings


def create_db_engine_and_session_factory():
    """
    Parses the DATABASE_URL and creates an async engine and session factory,
    correctly handling SSL configuration for asyncpg.
    """
    url_str = str(settings.DATABASE_URL)
    if not url_str:
        raise ValueError("DATABASE_URL not configured")

    parsed_url = urlparse(url_str)
    query_params = parse_qs(parsed_url.query)

    # Extract sslmode before creating async URL
    ssl_mode = query_params.get("sslmode", [None])[0]

    # Remove sslmode from query params (asyncpg doesn't accept it in URL)
    if "sslmode" in query_params:
        del query_params["sslmode"]

    # Rebuild query string without sslmode
    new_query = urlencode(query_params, doseq=True)

    # Create async URL without sslmode parameter
    async_url = parsed_url._replace(
        scheme=parsed_url.scheme.replace("postgresql", "postgresql+asyncpg", 1),
        query=new_query,
    ).geturl()

    connect_args = {}

    # Configure SSL for asyncpg via connect_args
    if ssl_mode and ssl_mode != "disable":
        if ssl_mode in ("require", "prefer", "allow"):
            # Simple SSL without certificate verification
            connect_args["ssl"] = True
        elif ssl_mode in ("verify-ca", "verify-full"):
            # Full SSL verification (requires certificate paths)
            # For production, you'd add certificate paths here
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = ssl_mode == "verify-full"
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            connect_args["ssl"] = ssl_context

    engine = create_async_engine(
        async_url,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Important for connection health checks
        connect_args=connect_args,
    )

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    return engine, session_factory


# Create global engine and session maker
engine, async_session_maker = create_db_engine_and_session_factory()


async def get_async_session():
    """Dependency for FastAPI routes to get a database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
