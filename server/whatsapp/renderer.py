"""
WhatsApp Message Renderer - server/whatsapp/renderer.py

Converts Pydantic commands to WhatsApp API dict payloads.
Simple, single-file approach - easy to debug and maintain.

Flow: Command (Pydantic) → render() → dict → OutboundClient
"""

from typing import Any, Dict

from server.schemas.outbound import (
    BaseOutboundMessage,
    InteractiveButtonsMessage,
    InteractiveListMessage,
    LocationMessage,
    MarkAsReadMessage,
    MediaMessage,
    OutboundMessage,
    ReactionMessage,
    TemplateMessage,
    TextMessage,
)

# =============================================================================
# RENDER FUNCTIONS
# =============================================================================


def _base_payload(cmd: BaseOutboundMessage) -> Dict[str, Any]:
    """Build common WhatsApp envelope."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": cmd.to_number.lstrip("+"),  # Meta expects no +
    }
    if cmd.reply_to_message_id:
        payload["context"] = {"message_id": cmd.reply_to_message_id}
    return payload


def render_text(cmd: TextMessage) -> Dict[str, Any]:
    """Render text message to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "text"
    payload["text"] = {
        "body": cmd.text,
        "preview_url": cmd.preview_url,
    }
    return payload


def render_template(cmd: TemplateMessage) -> Dict[str, Any]:
    """Render template message to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "template"
    payload["template"] = {
        "name": cmd.template_name,
        "language": {"code": cmd.language_code},
    }
    if cmd.components:
        payload["template"]["components"] = [c.model_dump() for c in cmd.components]
    return payload


def render_media(cmd: MediaMessage) -> Dict[str, Any]:
    """Render media message to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = cmd.media_type

    media_obj: Dict[str, Any] = {}
    if cmd.media_id:
        media_obj["id"] = cmd.media_id
    elif cmd.media_url:
        media_obj["link"] = cmd.media_url

    if cmd.caption and cmd.media_type in ("image", "video", "document"):
        media_obj["caption"] = cmd.caption
    if cmd.filename and cmd.media_type == "document":
        media_obj["filename"] = cmd.filename

    payload[cmd.media_type] = media_obj
    return payload


def render_interactive_buttons(cmd: InteractiveButtonsMessage) -> Dict[str, Any]:
    """Render interactive buttons to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "interactive"

    interactive: Dict[str, Any] = {
        "type": "button",
        "body": {"text": cmd.body_text},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": btn.id, "title": btn.title[:20]}}
                for btn in cmd.buttons
            ]
        },
    }

    if cmd.header_text:
        interactive["header"] = {"type": "text", "text": cmd.header_text[:60]}
    if cmd.footer_text:
        interactive["footer"] = {"text": cmd.footer_text[:60]}

    payload["interactive"] = interactive
    return payload


def render_interactive_list(cmd: InteractiveListMessage) -> Dict[str, Any]:
    """Render interactive list to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "interactive"

    interactive: Dict[str, Any] = {
        "type": "list",
        "body": {"text": cmd.body_text},
        "action": {
            "button": cmd.button_text[:20],
            "sections": [
                {
                    "title": section.title,
                    "rows": [
                        {
                            "id": row.id,
                            "title": row.title,
                            "description": row.description,
                        }
                        for row in section.rows
                    ],
                }
                for section in cmd.sections
            ],
        },
    }

    if cmd.header_text:
        interactive["header"] = {"type": "text", "text": cmd.header_text[:60]}
    if cmd.footer_text:
        interactive["footer"] = {"text": cmd.footer_text[:60]}

    payload["interactive"] = interactive
    return payload


def render_location(cmd: LocationMessage) -> Dict[str, Any]:
    """Render location message to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "location"
    payload["location"] = {
        "latitude": cmd.latitude,
        "longitude": cmd.longitude,
    }
    if cmd.name:
        payload["location"]["name"] = cmd.name
    if cmd.address:
        payload["location"]["address"] = cmd.address
    return payload


def render_reaction(cmd: ReactionMessage) -> Dict[str, Any]:
    """Render reaction message to WhatsApp dict."""
    payload = _base_payload(cmd)
    payload["type"] = "reaction"
    payload["reaction"] = {
        "message_id": cmd.target_message_id,
        "emoji": cmd.emoji,
    }
    return payload


def render_mark_as_read(cmd: MarkAsReadMessage) -> Dict[str, Any]:
    """Render mark-as-read to WhatsApp dict (special structure)."""
    return {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": cmd.target_message_id,
    }


# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================


def render(cmd: OutboundMessage) -> Dict[str, Any]:
    """
    Convert any Pydantic command to WhatsApp API dict.

    Args:
        cmd: Validated Pydantic message command

    Returns:
        Dict ready for WhatsApp Cloud API

    Raises:
        ValueError: If command type is unknown

    Example:
        >>> from server.schemas.outbound import TextMessage
        >>> cmd = TextMessage(message_id="1", workspace_id="1",
        ...                   phone_number_id="123", to_number="+1234567890",
        ...                   text="Hello!")
        >>> payload = render(cmd)
        >>> # payload is now ready for OutboundClient
    """
    if isinstance(cmd, TextMessage):
        return render_text(cmd)
    elif isinstance(cmd, TemplateMessage):
        return render_template(cmd)
    elif isinstance(cmd, MediaMessage):
        return render_media(cmd)
    elif isinstance(cmd, InteractiveButtonsMessage):
        return render_interactive_buttons(cmd)
    elif isinstance(cmd, InteractiveListMessage):
        return render_interactive_list(cmd)
    elif isinstance(cmd, LocationMessage):
        return render_location(cmd)
    elif isinstance(cmd, ReactionMessage):
        return render_reaction(cmd)
    elif isinstance(cmd, MarkAsReadMessage):
        return render_mark_as_read(cmd)
    else:
        raise ValueError(f"Unknown command type: {type(cmd).__name__}")
