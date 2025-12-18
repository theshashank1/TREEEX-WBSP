from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import (
    Base,
    CampaignStatus,
    MessageStatus,
    SoftDeleteMixin,
    TemplateStatus,
    TimestampMixin,
)


class Template(TimestampMixin, SoftDeleteMixin, Base):
    """Message templates - scoped to phone_number_id for Meta API registration."""

    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=TemplateStatus.PENDING.value, nullable=False
    )
    meta_template_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("workspace_members.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="templates"
    )
    phone_number: Mapped["PhoneNumber"] = relationship(
        "PhoneNumber", back_populates="templates"
    )
    creator: Mapped[Optional["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="created_templates"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign", back_populates="template"
    )

    __table_args__ = (
        Index(
            "idx_template_workspace_phone_name",
            "workspace_id",
            "phone_number_id",
            "name",
            unique=True,
        ),
        Index("idx_template_workspace_status", "workspace_id", "status"),
        Index("idx_template_workspace_category", "workspace_id", "category"),
        Index("idx_template_phone_status", "phone_number_id", "status"),
        Index("idx_template_phone", "phone_number_id"),
        Index("idx_template_components_gin", "components", postgresql_using="gin"),
    )


class Campaign(TimestampMixin, SoftDeleteMixin, Base):
    """Bulk messaging campaigns - scoped to phone number."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_contacts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    read_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=CampaignStatus.DRAFT.value, nullable=False
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("workspace_members.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="campaigns"
    )
    phone_number: Mapped["PhoneNumber"] = relationship(
        "PhoneNumber", back_populates="campaigns"
    )
    template: Mapped[Optional["Template"]] = relationship(
        "Template", back_populates="campaigns"
    )
    creator: Mapped[Optional["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="created_campaigns"
    )
    campaign_messages: Mapped[List["CampaignMessage"]] = relationship(
        "CampaignMessage", back_populates="campaign", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_campaign_workspace_status", "workspace_id", "status"),
        Index("idx_campaign_phone_status", "phone_number_id", "status"),
        Index("idx_campaign_scheduled", "scheduled_at"),
        Index("idx_campaign_workspace", "workspace_id"),
        Index("idx_campaign_phone", "phone_number_id"),
    )


class CampaignMessage(Base):
    """Individual campaign message tracking - no soft delete."""

    __tablename__ = "campaign_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="SET NULL"), nullable=True
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=MessageStatus.PENDING.value, nullable=False
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="campaign_messages"
    )
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="campaign_messages"
    )
    phone_number: Mapped[Optional["PhoneNumber"]] = relationship(
        "PhoneNumber", back_populates="campaign_messages"
    )
    message: Mapped[Optional["Message"]] = relationship(
        "Message", back_populates="campaign_message"
    )

    __table_args__ = (
        Index(
            "idx_camp_msg_campaign_contact", "campaign_id", "contact_id", unique=True
        ),
        Index("idx_camp_msg_campaign_status", "campaign_id", "status"),
        Index("idx_camp_msg_workspace", "workspace_id"),
        Index("idx_camp_msg_status", "status"),
    )
