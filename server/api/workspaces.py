from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.core.db import get_async_session
from server.core.supabase import Client, get_user
from server.dependencies import get_supabase_client
from server.models.access import User, Workspace, WorkspaceMember
from server.models.base import MemberRole, MemberStatus, utc_now
from server.schemas.workspaces import (
    AddMemberRequest,
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

# Dependencies
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SupabaseDep = Annotated[Client, Depends(get_supabase_client)]


async def get_current_user(session: SessionDep, supabase: SupabaseDep) -> User:
    """Get authenticated user from Supabase token and verify they exist in local database."""
    supabase_user = get_user(supabase)

    result = await session.execute(select(User).where(User.id == supabase_user.id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


async def get_workspace_with_permission(
    workspace_id: UUID,
    user_id: UUID,
    session: AsyncSession,
    required_roles: Optional[List[MemberRole]] = None,
) -> Workspace:
    """Get workspace and verify user has permission (membership check + optional role check)."""
    # Get workspace
    result = await session.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check membership
    result = await session.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.status == MemberStatus.ACTIVE.value,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    # Check role if required
    if required_roles:
        if member.role not in [r.value for r in required_roles]:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions for this action"
            )

    return workspace


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    data: WorkspaceCreate,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """Create a new workspace."""
    user = await get_current_user(session, supabase)

    try:
        # Create workspace (slug, api_key, webhook_secret are auto-generated)
        workspace = Workspace(
            name=data.name,
            created_by=user.id,
            plan=data.plan.value,
        )

        session.add(workspace)
        await session.flush()  # Get workspace ID before creating member

        # Add creator as OWNER member
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=MemberRole.OWNER.value,
            status=MemberStatus.ACTIVE.value,
            joined_at=utc_now(),
        )

        session.add(member)
        await session.commit()
        await session.refresh(workspace)

        return workspace

    except Exception:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Failed to create workspace")


@router.get("", response_model=List[WorkspaceListResponse])
async def list_workspaces(
    session: SessionDep,
    supabase: SupabaseDep,
):
    """List all workspaces user is a member of."""
    user = await get_current_user(session, supabase)

    # Get all memberships with workspace data
    result = await session.execute(
        select(WorkspaceMember, Workspace)
        .join(Workspace, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == MemberStatus.ACTIVE.value,
            Workspace.deleted_at.is_(None),
        )
    )

    workspaces_with_roles = result.all()

    return [
        WorkspaceListResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            plan=workspace.plan,
            status=workspace.status,
            created_at=workspace.created_at,
            user_role=member.role,
        )
        for member, workspace in workspaces_with_roles
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """Get specific workspace. Requires membership."""
    user = await get_current_user(session, supabase)

    workspace = await get_workspace_with_permission(
        workspace_id=workspace_id,
        user_id=user.id,
        session=session,
    )

    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """Update workspace. Requires OWNER or ADMIN role."""
    user = await get_current_user(session, supabase)

    workspace = await get_workspace_with_permission(
        workspace_id=workspace_id,
        user_id=user.id,
        session=session,
        required_roles=[MemberRole.OWNER, MemberRole.ADMIN],
    )

    try:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                # Convert enums to their values for database storage
                if hasattr(value, "value"):
                    value = value.value
                setattr(workspace, field, value)

        await session.commit()
        await session.refresh(workspace)

        return workspace

    except Exception:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Failed to update workspace")


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: UUID,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """Soft delete workspace. Requires OWNER role only."""
    user = await get_current_user(session, supabase)

    workspace = await get_workspace_with_permission(
        workspace_id=workspace_id,
        user_id=user.id,
        session=session,
        required_roles=[MemberRole.OWNER],
    )

    try:
        workspace.soft_delete()
        await session.commit()

    except Exception:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Failed to delete workspace")


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: UUID,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """List workspace members. Requires membership."""
    user = await get_current_user(session, supabase)

    # Verify user has access to workspace
    await get_workspace_with_permission(
        workspace_id=workspace_id,
        user_id=user.id,
        session=session,
    )

    result = await session.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.status == MemberStatus.ACTIVE.value,
        )
    )

    members = result.scalars().all()

    return members


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def add_workspace_member(
    workspace_id: UUID,
    data: AddMemberRequest,
    session: SessionDep,
    supabase: SupabaseDep,
):
    """Add member to workspace. Requires OWNER or ADMIN role."""
    user = await get_current_user(session, supabase)

    # Verify user has permission to add members
    await get_workspace_with_permission(
        workspace_id=workspace_id,
        user_id=user.id,
        session=session,
        required_roles=[MemberRole.OWNER, MemberRole.ADMIN],
    )

    # Find the user to add by email
    result = await session.execute(select(User).where(User.email == data.user_email))
    new_member_user = result.scalar_one_or_none()

    if not new_member_user:
        raise HTTPException(status_code=404, detail="User not found with this email")

    # Check if user is already a member
    result = await session.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == new_member_user.id,
        )
    )
    existing_member = result.scalar_one_or_none()

    if existing_member:
        raise HTTPException(
            status_code=400, detail="User is already a member of this workspace"
        )

    try:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=new_member_user.id,
            role=data.role.value,
            status=MemberStatus.ACTIVE.value,
            invited_by=user.id,
            invited_at=utc_now(),
            joined_at=utc_now(),
        )

        session.add(member)
        await session.commit()
        await session.refresh(member)

        return member

    except Exception:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Failed to add member")
