from __future__ import annotations
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, Index, Uuid, func
from sqlalchemy.dialects. postgresql import JSONB
from sqlalchemy. orm import Mapped, mapped_column, relationship

from .base import Base, utc_now


class WebhookLog(Base):
    """Webhook audit log with idempotency - no soft delete for audit trail."""
    __tablename__ = "webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    phone_number_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("phone_numbers.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        default=utc_now, server_default=func. now(), nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now, server_default=func.now(), onupdate=utc_now, nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="webhook_logs")
    phone_number: Mapped[Optional["PhoneNumber"]] = relationship("PhoneNumber")

    __table_args__ = (
        Index("idx_webhook_workspace_event", "workspace_id", "event_id_hash", unique=True),
        Index("idx_webhook_workspace_time", "workspace_id", "received_at"),
        Index("idx_webhook_phone_time", "phone_number_id", "received_at"),
        Index("idx_webhook_unprocessed", "processed", "received_at"),
        Index("idx_webhook_event_type", "event_type", "received_at"),
        Index("idx_webhook_payload_gin", "payload", postgresql_using="gin"),
    )