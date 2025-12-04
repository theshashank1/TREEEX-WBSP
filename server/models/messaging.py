from __future__ import annotations
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, Text, BigInteger, ForeignKey, Index, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
    utc_now,
    MessageStatus,
    ConversationStatus,
    ConversationType,
)


class Conversation(TimestampMixin, Base):
    """Message threads grouped by contact and phone number."""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=ConversationStatus.OPEN.value, nullable=False
    )
    conversation_type: Mapped[str] = mapped_column(
        String(30), default=ConversationType.USER_INITIATED.value, nullable=False
    )
    last_message_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    last_inbound_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    window_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("workspace_members.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="conversations")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="conversations")
    phone_number: Mapped["PhoneNumber"] = relationship("PhoneNumber", back_populates="conversations")
    assignee: Mapped[Optional["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="assigned_conversations"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conv_workspace_contact_phone", "workspace_id", "contact_id", "phone_number_id", unique=True),
        Index("idx_conv_workspace_status", "workspace_id", "status"),
        Index("idx_conv_workspace", "workspace_id"),
        Index("idx_conv_contact", "contact_id"),
        Index("idx_conv_assigned", "assigned_to"),
        Index("idx_conv_window", "window_expires_at"),
        Index("idx_conv_last_msg", "last_message_at"),
    )

    def is_window_open(self) -> bool:
        """Check if the 24-hour messaging window is still open."""
        if not self.window_expires_at:
            return False
        return utc_now() < self.window_expires_at


class MediaFile(TimestampMixin, SoftDeleteMixin, Base):
    """Media file metadata - actual files stored in R2/S3."""
    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    original_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("workspace_members.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="media_files")
    uploader: Mapped[Optional["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="uploaded_media"
    )
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="media")

    __table_args__ = (
        Index("idx_media_workspace", "workspace_id"),
        Index("idx_media_type", "type"),
    )


class Message(Base):
    """All WhatsApp messages - no soft delete for compliance."""
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid. uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False
    )
    wa_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)
    to_number: Mapped[str] = mapped_column(String(20), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    media_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=MessageStatus.PENDING.value, nullable=False
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("workspace_members.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now, server_default=func.now(), nullable=False
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="messages")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    phone_number: Mapped["PhoneNumber"] = relationship("PhoneNumber", back_populates="messages")
    media: Mapped[Optional["MediaFile"]] = relationship("MediaFile", back_populates="messages")
    sender: Mapped[Optional["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="sent_messages"
    )
    campaign_message: Mapped[Optional["CampaignMessage"]] = relationship(
        "CampaignMessage", back_populates="message", uselist=False
    )

    __table_args__ = (
        Index("idx_msg_conversation_time", "conversation_id", "created_at"),
        Index("idx_msg_conv_direction_time", "conversation_id", "direction", "created_at"),
        Index("idx_msg_wa_id", "wa_message_id"),
        Index("idx_msg_workspace_time", "workspace_id", "created_at"),
        Index("idx_msg_phone_time", "phone_number_id", "created_at"),
        Index("idx_msg_status", "status"),
        Index("idx_msg_direction", "direction"),
        Index("idx_msg_type", "type"),
        Index("idx_msg_sent_by", "sent_by"),
        Index("idx_msg_content_gin", "content", postgresql_using="gin"),
    )