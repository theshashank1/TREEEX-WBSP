"""
Main Application Entry Point - server/main.py

Configures FastAPI application, middleware, lifecycle events, and routers.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from supabase import create_client

# Import routers
from server.api import (
    admin,
    auth,
    campaigns,
    contacts,
    media,
    messages,
    phone_numbers,
    templates,
    webhooks,
    workspaces,
)
from server.core import redis as redis_client
from server.core.config import settings
from server.core.supabase import get_supabase_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await redis_client.startup()
    app.state.supabase = get_supabase_client()

    # Initialize Supabase Client and store in app.state
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        app.state.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    yield

    # --- Shutdown ---
    await redis_client.shutdown()


# Initialize Sentry

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

else:
    raise ValueError("SENTRY_DSN is not set in the environment")

app = FastAPI(
    title="TREEEX WhatsApp BSP",
    description="WhatsApp Business Solution Provider API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PROD: Restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint. Returns 200 if running."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint. Returns 200 if ready."""
    return {"status": "ready"}


@app.get("/sentry-debug", tags=["Health"])
async def trigger_error():
    """Trigger an error to test Sentry integration."""
    return 1 / 0


# =============================================================================
# Register API Routers
# =============================================================================

app.include_router(webhooks.router)
app.include_router(auth.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(phone_numbers.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
