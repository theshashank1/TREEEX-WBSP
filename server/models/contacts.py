from __future__ import annotations
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, Index, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin, PhoneNumberQuality

class PhoneNumber(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "phone_numbers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    quality_rating: Mapped[str] = mapped_column(String(10), default=PhoneNumberQuality.GREEN.value, nullable=False)
    message_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="phone_numbers")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="phone_number")

    __table_args__ = (
        Index("idx_phone_workspace_number", "workspace_id", "phone_number", unique=True),
        Index("idx_phone_number_id", "phone_number_id"),
    )

class Contact(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    wa_id: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_pic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opted_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opt_in_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opt_in_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="contacts")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="contact", cascade="all, delete-orphan")
    campaign_messages: Mapped[List["CampaignMessage"]] = relationship("CampaignMessage", back_populates="contact")

    __table_args__ = (
        Index("idx_contact_workspace_waid", "workspace_id", "wa_id", unique=True),
        Index("idx_contact_tags_gin", "tags", postgresql_using="gin"),
        Index("idx_contact_custom_fields_gin", "custom_fields", postgresql_using="gin"),
    )