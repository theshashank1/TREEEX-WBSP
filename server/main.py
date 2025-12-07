from contextlib import asynccontextmanager

from fastapi import FastAPI
from supabase import create_client

# Import routers
from server.api import auth, campaigns, media, messages, phone_numbers, webhooks
from server.core import redis as redis_client
from server.core.config import settings
from server.core.supabase import get_supabase_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await redis_client.startup()
    # init_db()
    app.state.supabase = get_supabase_client()

    # Initialize Supabase Client and store in app.state
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        app.state.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    yield

    # --- Shutdown ---

    await redis_client.shutdown()


app = FastAPI(lifespan=lifespan)

# Register Routers
app.include_router(webhooks.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(phone_numbers.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
