from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import (
    Base,
    PhoneNumberQuality,
    PhoneNumberStatus,
    SoftDeleteMixin,
    TimestampMixin,
)


class Channel(TimestampMixin, SoftDeleteMixin, Base):
    """WhatsApp Channels (formerly PhoneNumber) with Meta credentials."""

    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="WhatsApp Channel"
    )

    # Meta Configuration
    meta_phone_number_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    meta_business_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_waba_id: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # Added for future use if needed, though waba_id was used in schema

    access_token: Mapped[str] = mapped_column(Text, nullable=False)

    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status & Quality
    quality_rating: Mapped[str] = mapped_column(
        String(10), default=PhoneNumberQuality.GREEN.value, nullable=False
    )
    message_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=PhoneNumberStatus.PENDING.value, nullable=False
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="channels"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="channel", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="channel", cascade="all, delete-orphan"
    )
    templates: Mapped[List["Template"]] = relationship(
        "Template", back_populates="channel", cascade="all, delete-orphan"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign", back_populates="channel", cascade="all, delete-orphan"
    )
    campaign_messages: Mapped[List["CampaignMessage"]] = relationship(
        "CampaignMessage", back_populates="channel"
    )
    contact_states: Mapped[List["ContactChannelState"]] = relationship(
        "ContactChannelState", back_populates="channel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_channel_workspace_number", "workspace_id", "phone_number", unique=True
        ),
        Index("idx_channel_workspace", "workspace_id"),
        Index("idx_channel_status", "status"),
        Index("idx_channel_meta_id", "meta_phone_number_id"),
    )


class Contact(TimestampMixin, SoftDeleteMixin, Base):
    """
    Customer identity - workspace-scoped.

    Contacts belong to the workspace (business), not to a specific channel.
    Messaging permissions are tracked separately via ContactChannelState.
    """

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    wa_id: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source attribution - which channel first acquired this contact
    source_channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("channels.id", ondelete="SET NULL"), nullable=True
    )

    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="contacts"
    )
    source_channel: Mapped[Optional["Channel"]] = relationship(
        "Channel", foreign_keys=[source_channel_id]
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="contact", cascade="all, delete-orphan"
    )
    campaign_messages: Mapped[List["CampaignMessage"]] = relationship(
        "CampaignMessage", back_populates="contact"
    )
    channel_states: Mapped[List["ContactChannelState"]] = relationship(
        "ContactChannelState", back_populates="contact", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_contact_workspace_waid", "workspace_id", "wa_id", unique=True),
        Index("idx_contact_workspace", "workspace_id"),
        Index("idx_contact_source_channel", "source_channel_id"),
        Index("idx_contact_updated", "updated_at"),
        Index("idx_contact_tags_gin", "tags", postgresql_using="gin"),
        Index("idx_contact_custom_fields_gin", "custom_fields", postgresql_using="gin"),
    )


class ContactChannelState(TimestampMixin, Base):
    """
    Per-channel execution state for contacts.

    Tracks messaging permissions, opt-in status, blocking, and last interaction
    for each (contact, channel) pair.
    """

    __tablename__ = "contact_channel_states"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )

    # Messaging permissions
    opt_in_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_in_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Values: "explicit", "implicit", "inbound", "transactional"
    opt_in_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Interaction State (for 24h window)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="channel_states"
    )
    channel: Mapped["Channel"] = relationship(
        "Channel", back_populates="contact_states"
    )

    __table_args__ = (
        Index(
            "idx_ccs_contact_channel",
            "contact_id",
            "channel_id",
            unique=True,
        ),
        Index("idx_ccs_channel_optin", "channel_id", "opt_in_status"),
        Index("idx_ccs_workspace_contact", "workspace_id", "contact_id"),
        Index("idx_ccs_workspace", "workspace_id"),
    )
