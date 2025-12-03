from __future__ import annotations
import uuid
import enum
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, func, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ============================================================================
# UTILITIES
# ============================================================================

def utc_now() -> datetime:
    """Current UTC time as naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def generate_slug(name: str) -> str:
    """Generate URL-friendly slug with unique suffix."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{suffix}" if slug else f"workspace-{suffix}"

# ============================================================================
# ENUMS
# ============================================================================

class WorkspacePlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class WorkspaceStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class MemberRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    AGENT = "AGENT"

class MemberStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class PhoneNumberQuality(str, enum.Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"

class MessageDirection(str, enum.Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class TemplateCategory(str, enum.Enum):
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"
    AUTHENTICATION = "AUTHENTICATION"

class TemplateStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISABLED = "DISABLED"

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ============================================================================
# BASE & MIXINS
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all models."""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, (datetime, uuid.UUID)):
                val = str(val)
            if isinstance(val, enum.Enum):
                val = val.value
            result[col.name] = val
        return result

class TimestampMixin:
    """Standard created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=utc_now, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=utc_now, server_default=func.now(), onupdate=utc_now, nullable=False
    )

class SoftDeleteMixin:
    """Soft delete support."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = utc_now()

    def restore(self):
        self.deleted_at = None