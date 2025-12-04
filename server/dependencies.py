# We use 'Any' here to avoid hard dependency on supabase-py if not installed locally during dev,
# but normally you would import: from supabase import Client
from typing import Any

from fastapi import Request


def get_supabase_client(request: Request) -> Any:
    """
    Dependency to get the Supabase client from app state.
    Initialized in main.py lifespan.
    """
    if not hasattr(request.app.state, "supabase"):
        raise RuntimeError("Supabase client is not initialized in app.state")
    return request.app.state.supabase
