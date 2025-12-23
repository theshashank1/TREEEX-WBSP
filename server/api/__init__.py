"""
API routers for the TREEEX WhatsApp BSP platform.
"""

from server.api import (
    admin,
    auth,
    campaigns,
    channels,
    contacts,
    media,
    messages,
    templates,
    webhooks,
    workspaces,
)

__all__ = [
    "admin",
    "auth",
    "campaigns",
    "contacts",
    "media",
    "messages",
    "channels",
    "templates",
    "webhooks",
    "workspaces",
]
