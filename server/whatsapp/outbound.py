"""
WhatsApp Outbound Messaging Client - server/whatsapp/outbound.py

Production-ready client for sending all types of WhatsApp messages via Cloud API.
Handles: Text, Templates, Media, Interactive (Buttons/Lists), Location, Reactions.

Usage:
    from server.whatsapp.outbound import OutboundClient

    client = OutboundClient(access_token="...", phone_number_id="...")
    wa_msg_id, error = await client.send_text_message(
        to_number="+15551234567",
        text="Hello from WhatsApp!"
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx

from server.core.config import settings
from server.core.monitoring import log_event, log_exception

# Meta Graph API configuration
DEFAULT_API_VERSION = "v22.0"
META_GRAPH_API_BASE = "https://graph.facebook.com"
HTTP_TIMEOUT = 30.0


@dataclass
class MetaAPIError:
    """Error details from Meta Graph API."""

    code: int
    message: str
    error_subcode: Optional[int] = None
    is_retryable: bool = False

    @classmethod
    def from_response(cls, response: httpx.Response, data: dict) -> "MetaAPIError":
        """Create MetaAPIError from API response."""
        error_data = data.get("error", {})
        code = error_data.get("code", response.status_code)

        # Determine if error is retryable (rate limit or server errors)
        is_retryable = response.status_code in (429, 500, 502, 503, 504) or code in (
            1,  # Unknown error
            2,  # Service temporarily unavailable
            4,  # Rate limit hit
            17,  # User request limit reached
            341,  # Application limit reached
            368,  # Temporarily blocked
            130429,  # Cloud API rate limit
        )

        return cls(
            code=code,
            message=error_data.get("message", "Unknown error"),
            error_subcode=error_data.get("error_subcode"),
            is_retryable=is_retryable,
        )


@dataclass
class SendResult:
    """Result of a send operation."""

    wa_message_id: Optional[str] = None
    error: Optional[MetaAPIError] = None

    @property
    def success(self) -> bool:
        return self.wa_message_id is not None and self.error is None


class OutboundClient:
    """
    WhatsApp Cloud API client for outbound messaging.
    Thread-safe and async.
    """

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        api_version: Optional[str] = None,
    ):
        """Initialize OutboundClient."""
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = (
            api_version or settings.META_API_VERSION or DEFAULT_API_VERSION
        )
        self.base_url = f"{META_GRAPH_API_BASE}/{self.api_version}"
        self.messages_url = f"{self.base_url}/{phone_number_id}/messages"

    # =========================================================================
    # CORE SEND METHOD
    # =========================================================================

    async def _send_message(
        self,
        payload: Dict[str, Any],
        message_type: str,
    ) -> SendResult:
        """Core method to send any message type to WhatsApp API."""
        # Ensure required fields
        payload["messaging_product"] = "whatsapp"

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    self.messages_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                data = response.json()

                if response.status_code not in (200, 201):
                    error = MetaAPIError.from_response(response, data)
                    log_event(
                        "whatsapp_send_failed",
                        level="warning",
                        message_type=message_type,
                        status_code=response.status_code,
                        error_code=error.code,
                    )
                    return SendResult(error=error)

                # Extract message ID from response
                messages = data.get("messages", [])
                if not messages:
                    log_event(
                        "whatsapp_send_no_message_id",
                        level="error",
                        message_type=message_type,
                        response=data,
                    )
                    return SendResult(
                        error=MetaAPIError(
                            code=-1,
                            message="No message ID in response",
                        )
                    )

                wa_message_id = messages[0].get("id")

                log_event(
                    "whatsapp_send_success",
                    level="debug",
                    message_type=message_type,
                    wa_message_id=wa_message_id,
                )

                return SendResult(wa_message_id=wa_message_id)

        except httpx.TimeoutException:
            log_exception("whatsapp_send_timeout", message_type=message_type)
            return SendResult(
                error=MetaAPIError(
                    code=-1,
                    message="Request timed out",
                    is_retryable=True,
                )
            )
        except httpx.RequestError as e:
            log_exception("whatsapp_send_network_error", e, message_type=message_type)
            return SendResult(
                error=MetaAPIError(
                    code=-1,
                    message=f"Network error: {str(e)}",
                    is_retryable=True,
                )
            )
        except Exception as e:
            log_exception("whatsapp_send_error", e, message_type=message_type)
            return SendResult(
                error=MetaAPIError(
                    code=-1,
                    message=f"Unexpected error: {str(e)}",
                )
            )

    # =========================================================================
    # TEXT MESSAGES
    # =========================================================================

    async def send_text_message(
        self,
        to_number: str,
        text: str,
        preview_url: bool = False,
        reply_to_message_id: Optional[str] = None,
    ) -> SendResult:
        """Send a text message."""
        payload: Dict[str, Any] = {
            "to": to_number.lstrip("+"),  # Meta expects number without +
            "type": "text",
            "text": {
                "body": text,
                "preview_url": preview_url,
            },
        }

        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}

        return await self._send_message(payload, "text")

    # =========================================================================
    # TEMPLATE MESSAGES
    # =========================================================================

    async def send_template_message(
        self,
        to_number: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> SendResult:
        """Send a pre-approved template message."""
        template: Dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }

        if components:
            template["components"] = components

        payload = {
            "to": to_number.lstrip("+"),
            "type": "template",
            "template": template,
        }

        return await self._send_message(payload, "template")

    # =========================================================================
    # MEDIA MESSAGES
    # =========================================================================

    async def send_media_message(
        self,
        to_number: str,
        media_type: Literal["image", "video", "audio", "document", "sticker"],
        media_url: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
    ) -> SendResult:
        """
        Send a media message.
        Must provide either media_url OR media_id.
        """
        if not media_url and not media_id:
            return SendResult(
                error=MetaAPIError(
                    code=400,
                    message="Either media_url or media_id is required",
                )
            )

        media_object: Dict[str, Any] = {}

        if media_id:
            media_object["id"] = media_id
        else:
            media_object["link"] = media_url

        # Caption only supported for image, video, document
        if caption and media_type in ("image", "video", "document"):
            media_object["caption"] = caption

        # Filename only for documents
        if filename and media_type == "document":
            media_object["filename"] = filename

        payload: Dict[str, Any] = {
            "to": to_number.lstrip("+"),
            "type": media_type,
            "whatsapp": media_object,
            media_type: media_object,
        }

        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}

        return await self._send_message(payload, media_type)

    # =========================================================================
    # INTERACTIVE MESSAGES
    # =========================================================================

    async def send_interactive_buttons(
        self,
        to_number: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
    ) -> SendResult:
        """Send an interactive message with reply buttons (max 3)."""
        if len(buttons) > 3:
            return SendResult(
                error=MetaAPIError(
                    code=400,
                    message="Maximum 3 buttons allowed",
                )
            )

        if len(buttons) < 1:
            return SendResult(
                error=MetaAPIError(
                    code=400,
                    message="At least 1 button is required",
                )
            )

        interactive: Dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"][:20],  # Truncate to max length
                        },
                    }
                    for btn in buttons
                ]
            },
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text[:60]}

        if footer_text:
            interactive["footer"] = {"text": footer_text[:60]}

        payload: Dict[str, Any] = {
            "to": to_number.lstrip("+"),
            "type": "interactive",
            "interactive": interactive,
        }

        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}

        return await self._send_message(payload, "interactive_buttons")

    async def send_interactive_list(
        self,
        to_number: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
    ) -> SendResult:
        """Send an interactive list message."""
        if len(sections) > 10:
            return SendResult(
                error=MetaAPIError(
                    code=400,
                    message="Maximum 10 sections allowed",
                )
            )

        interactive: Dict[str, Any] = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections,
            },
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text[:60]}

        if footer_text:
            interactive["footer"] = {"text": footer_text[:60]}

        payload: Dict[str, Any] = {
            "to": to_number.lstrip("+"),
            "type": "interactive",
            "interactive": interactive,
        }

        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}

        return await self._send_message(payload, "interactive_list")

    # =========================================================================
    # LOCATION MESSAGE
    # =========================================================================

    async def send_location(
        self,
        to_number: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
    ) -> SendResult:
        """Send a location pin."""
        location: Dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
        }

        if name:
            location["name"] = name
        if address:
            location["address"] = address

        payload: Dict[str, Any] = {
            "to": to_number.lstrip("+"),
            "type": "location",
            "location": location,
        }

        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}

        return await self._send_message(payload, "location")

    # =========================================================================
    # REACTION MESSAGE
    # =========================================================================

    async def send_reaction(
        self,
        to_number: str,
        message_id: str,
        emoji: str,
    ) -> SendResult:
        """Send a reaction emoji to an existing message."""
        payload = {
            "to": to_number.lstrip("+"),
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji,
            },
        }

        return await self._send_message(payload, "reaction")

    # =========================================================================
    # MARK AS READ
    # =========================================================================

    async def mark_as_read(self, message_id: str) -> SendResult:
        """Mark an incoming message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    self.messages_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                data = response.json()

                if response.status_code not in (200, 201):
                    error = MetaAPIError.from_response(response, data)
                    log_event(
                        "whatsapp_mark_read_failed",
                        level="warning",
                        message_id=message_id,
                        error_code=error.code,
                    )
                    return SendResult(error=error)

                log_event(
                    "whatsapp_mark_read_success",
                    level="debug",
                    message_id=message_id,
                )

                return SendResult(wa_message_id=message_id)

        except Exception as e:
            log_exception("whatsapp_mark_read_error", e)
            return SendResult(
                error=MetaAPIError(
                    code=-1,
                    message=f"Failed to mark as read: {str(e)}",
                )
            )


# =============================================================================
# CONVENIENCE FUNCTION FOR QUICK SENDS
# =============================================================================


async def send_message(
    access_token: str,
    phone_number_id: str,
    to_number: str,
    message_type: str,
    **kwargs,
) -> SendResult:
    """Convenience function to send a message without creating a client instance."""
    client = OutboundClient(access_token, phone_number_id)

    method_map = {
        "text": client.send_text_message,
        "template": client.send_template_message,
        "image": lambda **kw: client.send_media_message(media_type="image", **kw),
        "video": lambda **kw: client.send_media_message(media_type="video", **kw),
        "audio": lambda **kw: client.send_media_message(media_type="audio", **kw),
        "document": lambda **kw: client.send_media_message(media_type="document", **kw),
        "sticker": lambda **kw: client.send_media_message(media_type="sticker", **kw),
        "interactive_buttons": client.send_interactive_buttons,
        "interactive_list": client.send_interactive_list,
        "location": client.send_location,
        "reaction": client.send_reaction,
    }

    method = method_map.get(message_type)
    if not method:
        return SendResult(
            error=MetaAPIError(
                code=400,
                message=f"Unknown message type: {message_type}",
            )
        )

    return await method(to_number=to_number, **kwargs)
