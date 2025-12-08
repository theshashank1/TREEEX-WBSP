from enum import Enum

# ============================================================================
# EVENT TYPES
# ============================================================================


class WebhookEventType(str, Enum):
    """Meta WhatsApp webhook event types"""

    MESSAGE = "message"
    STATUS = "status"
    ERROR = "error"
    TEMPLATE_STATUS = "template_status"
    HISTORY = "history"
    TRACKING = "tracking"
    UNKNOWN = "unknown"


__all__ = [
    WebhookEventType,
]
