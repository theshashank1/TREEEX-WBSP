from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.supabase import Client, get_user
from server.dependencies import get_supabase_client
from server.models.access import User
from server.schemas.auth import *

router = APIRouter(prefix="/auth", tags=["Authentication"])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


@router.post("/signup", response_model=SignupResponse)
async def signup(
    data: Signup,
    session: SessionDep,
    supabase: SupabaseDep,
    provider: Provider = Provider.email,
):
    if provider != Provider.email:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        # Create user in Supabase Auth
        response = supabase.auth.sign_up(
            {"email": data.email, "password": data.password}
        )

        if not response.user:
            raise HTTPException(status_code=400, detail="Sign-up failed")

        # Create user in local Postgres
        display_name = data.name or data.email.split("@")[0]

        user = User(
            id=response.user.id,
            email=data.email,
            name=display_name,
            email_verified=response.user.email_confirmed_at is not None,
            is_active=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return SignupResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=SigninResponse)
async def signin(
    data: Signup,
    session: SessionDep,
    supabase: SupabaseDep,
    provider: Provider = Provider.email,
):
    if provider != Provider.email:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Fetch local user
        result = await session.execute(select(User).where(User.id == response.user.id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        # Update login stats
        user.email_verified = response.user.email_confirmed_at is not None
        user.last_login_at = datetime.now()

        await session.commit()
        await session.refresh(user)

        return SigninResponse(
            user_id=response.user.id,
            access_token=response.session.access_token,
        )
    except Exception as e:
        await session.rollback()
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/refresh")
async def refresh(supabase: SupabaseDep):
    return supabase.auth.refresh_session()


@router.get("/me")
async def me(supabase: SupabaseDep):
    return get_user(supabase)
