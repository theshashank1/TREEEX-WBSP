from __future__ import annotations
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, Index, Uuid, text
from sqlalchemy. dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    WorkspacePlan,
    WorkspaceStatus,
    MemberRole,
    MemberStatus,
    generate_slug
)


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    owned_workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace", back_populates="owner", foreign_keys="Workspace.created_by"
    )
    memberships: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="user", foreign_keys="WorkspaceMember.user_id",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
    )


class Workspace(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    api_key: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    webhook_secret: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(20), default=WorkspacePlan.FREE.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=WorkspaceStatus.ACTIVE. value, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_workspaces", foreign_keys=[created_by])
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )
    phone_numbers: Mapped[List["PhoneNumber"]] = relationship(
        "PhoneNumber", back_populates="workspace", cascade="all, delete-orphan"
    )
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="workspace", cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="workspace", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="workspace", cascade="all, delete-orphan"
    )
    media_files: Mapped[List["MediaFile"]] = relationship(
        "MediaFile", back_populates="workspace", cascade="all, delete-orphan"
    )
    templates: Mapped[List["Template"]] = relationship(
        "Template", back_populates="workspace", cascade="all, delete-orphan"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign", back_populates="workspace", cascade="all, delete-orphan"
    )
    webhook_logs: Mapped[List["WebhookLog"]] = relationship(
        "WebhookLog", back_populates="workspace", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_workspace_api_key", "api_key"),
        Index("idx_workspace_status", "status"),
        Index("idx_workspace_created_by", "created_by"),
        Index("idx_workspace_slug", "slug"),
    )

    def __init__(self, **kwargs):
        if "slug" not in kwargs and "name" in kwargs:
            kwargs["slug"] = generate_slug(kwargs["name"])
        super().__init__(**kwargs)


class WorkspaceMember(TimestampMixin, Base):
    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), default=MemberRole.MEMBER. value, nullable=False)
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invited_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=MemberStatus.ACTIVE.value, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by])
    assigned_conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="assignee"
    )
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender"
    )
    uploaded_media: Mapped[List["MediaFile"]] = relationship(
        "MediaFile", back_populates="uploader"
    )
    created_templates: Mapped[List["Template"]] = relationship(
        "Template", back_populates="creator"
    )
    created_campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign", back_populates="creator"
    )

    __table_args__ = (
        Index("idx_member_workspace_user", "workspace_id", "user_id", unique=True),
        Index("idx_member_workspace", "workspace_id"),
        Index("idx_member_user", "user_id"),
        Index("idx_member_role", "role"),
        Index("idx_member_status", "status"),
    )