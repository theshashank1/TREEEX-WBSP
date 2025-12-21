# server/dependencies.py

# We use 'Any' here to avoid hard dependency on supabase-py if not installed locally during dev,
# but normally you would import: from supabase import Client
from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.models.access import User, WorkspaceMember
from server.models.base import MemberRole, MemberStatus


def get_supabase_client(request: Request) -> Any:
    """Get initialized Supabase client from app state."""
    if not hasattr(request.app.state, "supabase"):
        raise RuntimeError("Supabase client is not initialized in app.state")
    return request.app.state.supabase


# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Extract and verify user from Supabase JWT.

    Verifies token with Supabase and fetches user from local DB.
    Raises 401 if invalid or inactive.
    """
    supabase = get_supabase_client(request)

    try:
        # Verify the JWT token with Supabase
        token = credentials.credentials
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": "Invalid or expired token.",
                },
            )

        user_id = response.user.id

        # Fetch user from local database
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "USER_NOT_FOUND",
                    "message": "User not found in database.",
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "USER_INACTIVE",
                    "message": "User account is inactive.",
                },
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token."},
        )


async def get_workspace_member(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> WorkspaceMember:
    """
    Verify user is a member of the specified workspace.

    Raises 403 if access denied.
    """
    result = await session.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.status == MemberStatus.ACTIVE.value,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORKSPACE_ACCESS_DENIED",
                "message": "You are not a member of this workspace.",
            },
        )

    return member


async def require_workspace_admin(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> WorkspaceMember:
    """
    Verify user has OWNER or ADMIN role in the specified workspace.

    Raises 403 if permission denied.
    """
    member = await get_workspace_member(workspace_id, current_user, session)

    if member.role not in [MemberRole.OWNER.value, MemberRole.ADMIN.value]:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "You need OWNER or ADMIN role to perform this action.",
            },
        )

    return member


class WorkspaceMemberDep:
    """Callable dependency for workspace member verification."""

    def __init__(self, require_admin: bool = False):
        self.require_admin = require_admin

    async def __call__(
        self,
        workspace_id: UUID,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session),
    ) -> WorkspaceMember:
        if self.require_admin:
            return await require_workspace_admin(workspace_id, current_user, session)
        return await get_workspace_member(workspace_id, current_user, session)
