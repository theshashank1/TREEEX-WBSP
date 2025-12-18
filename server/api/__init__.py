"""
API routers for the TREEEX WhatsApp BSP platform.
"""

from server.api import (
    auth,
    broadcasts,
    campaigns,
    contacts,
    media,
    messages,
    phone_numbers,
    templates,
    webhooks,
    workspaces,
)

__all__ = [
    "auth",
    "broadcasts",
    "campaigns",
    "contacts",
    "media",
    "messages",
    "phone_numbers",
    "templates",
    "webhooks",
    "workspaces",
]
