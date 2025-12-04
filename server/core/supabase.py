import os
from typing import Optional

from fastapi import HTTPException
from supabase import Client, create_client

from server.core.config import settings

# Fetch environment variables
url: Optional[str] = settings.SUPABASE_URL
key: Optional[str] = settings.SUPABASE_SECRET_KEY

# Ensure Supabase credentials are available
if not url or not key:
    raise RuntimeError("Supabase environment variables are not set properly.")


def get_supabase_client() -> Client:
    """
    Get a new Supabase client.

    Returns:
        Client: Supabase client instance

    Raises:
        HTTPException: If Supabase configuration is missing
    """
    try:
        return create_client(url, key)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create Supabase client: {str(e)}"
        )


def get_user(client: Client):
    """
    Get the current user from Supabase.

    Returns:
        dict: User information

    Raises:
        HTTPException: If user is not authenticated or
        if there's an error fetching user data
    """
    try:
        supabase = client
        response = supabase.auth.get_user()

        if response is None or response.user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        return response.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user data: {str(e)}"
        )

    """Example usage
    from fastapi import Depends
    from app.utils.supabase import get_user, Client

    @app.get("/user/me")
    async def get_current_user(client: Client = Depends(get_supabase_client)):
        user = await get_user(client)
        return user
    """
