from __future__ import annotations
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Boolean, Text, ForeignKey, Index, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utc_now

class WebhookLog(Base):
    """
    Audit log for webhooks - No Soft Delete.
    """
    __tablename__ = "webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    received_at: Mapped[datetime] = mapped_column(default=utc_now, server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, server_default=func.now(), onupdate=utc_now, nullable=False)

    # Use String reference "Workspace" to avoid circular imports
    workspace: Mapped["Workspace"] = relationship("Workspace")

    __table_args__ = (
        Index("idx_webhook_workspace_event", "workspace_id", "event_id_hash", unique=True),
        Index("idx_webhook_payload_gin", "payload", postgresql_using="gin"),
    )