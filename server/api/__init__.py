"""
API routers for the TREEEX WhatsApp BSP platform.
"""

from server.api import (
    auth,
    campaigns,
    media,
    messages,
    phone_numbers,
    templates,
    webhooks,
    workspaces,
)

__all__ = [
    "auth",
    "workspaces",
    "phone_numbers",
    "webhooks",
    "campaigns",
    "media",
    "messages",
    "templates",
]
