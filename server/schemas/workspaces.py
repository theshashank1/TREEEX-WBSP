from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from server.models.base import MemberRole, MemberStatus, WorkspacePlan, WorkspaceStatus


class WorkspaceCreate(BaseModel):
    """Request model for creating a workspace"""

    name: str = Field(..., min_length=1, max_length=255)
    plan: WorkspacePlan = WorkspacePlan.FREE


class WorkspaceUpdate(BaseModel):
    """Request model for updating a workspace"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    plan: Optional[WorkspacePlan] = None
    status: Optional[WorkspaceStatus] = None
    settings: Optional[dict[str, Any]] = None


class WorkspaceMemberResponse(BaseModel):
    """Response model for workspace member"""

    id: UUID
    user_id: UUID
    role: MemberRole
    status: MemberStatus
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceResponse(BaseModel):
    """Full workspace response"""

    id: UUID
    name: str
    slug: str
    api_key: UUID
    webhook_secret: UUID
    created_by: UUID
    plan: WorkspacePlan
    status: WorkspaceStatus
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """Summarized workspace info with user's role"""

    id: UUID
    name: str
    slug: str
    plan: WorkspacePlan
    status: WorkspaceStatus
    created_at: datetime
    user_role: MemberRole

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    """Request model for adding a member to a workspace"""

    user_email: EmailStr
    role: MemberRole = MemberRole.MEMBER
