"""
Tests for WhatsApp Renderer - tests/test_renderer.py

Tests the Command → dict rendering logic.
"""

import pytest

from server.schemas.outbound import (
    Button,
    InteractiveButtonsMessage,
    InteractiveListMessage,
    ListRow,
    ListSection,
    LocationMessage,
    MarkAsReadMessage,
    MediaMessage,
    ReactionMessage,
    TemplateMessage,
    TextMessage,
)
from server.whatsapp.renderer import render

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def base_fields():
    """Common fields for all message types."""
    return {
        "message_id": "test-uuid-123",
        "workspace_id": "workspace-456",
        "phone_number_id": "123456789",
        "to_number": "+1234567890",
    }


# =============================================================================
# TEXT MESSAGE TESTS
# =============================================================================


def test_render_text_message(base_fields):
    """Test text message rendering."""
    cmd = TextMessage(**base_fields, text="Hello, World!")

    payload = render(cmd)

    assert payload["messaging_product"] == "whatsapp"
    assert payload["recipient_type"] == "individual"
    assert payload["to"] == "1234567890"  # + stripped
    assert payload["type"] == "text"
    assert payload["text"]["body"] == "Hello, World!"
    assert payload["text"]["preview_url"] is False


def test_render_text_with_preview(base_fields):
    """Test text message with URL preview enabled."""
    cmd = TextMessage(
        **base_fields, text="Check this: https://example.com", preview_url=True
    )

    payload = render(cmd)

    assert payload["text"]["preview_url"] is True


def test_render_text_with_reply(base_fields):
    """Test text message as reply."""
    cmd = TextMessage(**base_fields, text="Reply!", reply_to_message_id="wamid.xxx")

    payload = render(cmd)

    assert payload["context"]["message_id"] == "wamid.xxx"


# =============================================================================
# TEMPLATE MESSAGE TESTS
# =============================================================================


def test_render_template_message(base_fields):
    """Test template message rendering."""
    cmd = TemplateMessage(
        **base_fields,
        template_name="hello_world",
        language_code="en",
    )

    payload = render(cmd)

    assert payload["type"] == "template"
    assert payload["template"]["name"] == "hello_world"
    assert payload["template"]["language"]["code"] == "en"


# =============================================================================
# MEDIA MESSAGE TESTS
# =============================================================================


def test_render_media_with_url(base_fields):
    """Test media message with URL."""
    cmd = MediaMessage(
        **base_fields,
        media_type="image",
        media_url="https://example.com/image.jpg",
        caption="A photo",
    )

    payload = render(cmd)

    assert payload["type"] == "image"
    assert payload["image"]["link"] == "https://example.com/image.jpg"
    assert payload["image"]["caption"] == "A photo"


def test_render_media_with_id(base_fields):
    """Test media message with Meta media ID."""
    cmd = MediaMessage(
        **base_fields,
        media_type="document",
        media_id="media-id-123",
        filename="report.pdf",
    )

    payload = render(cmd)

    assert payload["type"] == "document"
    assert payload["document"]["id"] == "media-id-123"
    assert payload["document"]["filename"] == "report.pdf"


# =============================================================================
# INTERACTIVE MESSAGE TESTS
# =============================================================================


def test_render_interactive_buttons(base_fields):
    """Test interactive buttons rendering."""
    cmd = InteractiveButtonsMessage(
        **base_fields,
        body_text="Choose an option:",
        buttons=[
            Button(id="btn1", title="Option 1"),
            Button(id="btn2", title="Option 2"),
        ],
        header_text="Menu",
        footer_text="Select one",
    )

    payload = render(cmd)

    assert payload["type"] == "interactive"
    assert payload["interactive"]["type"] == "button"
    assert payload["interactive"]["body"]["text"] == "Choose an option:"
    assert len(payload["interactive"]["action"]["buttons"]) == 2
    assert payload["interactive"]["header"]["text"] == "Menu"
    assert payload["interactive"]["footer"]["text"] == "Select one"


def test_render_interactive_list(base_fields):
    """Test interactive list rendering."""
    cmd = InteractiveListMessage(
        **base_fields,
        body_text="Select from list:",
        button_text="View",
        sections=[
            ListSection(
                title="Section 1",
                rows=[
                    ListRow(id="row1", title="Item 1", description="First item"),
                    ListRow(id="row2", title="Item 2"),
                ],
            ),
        ],
    )

    payload = render(cmd)

    assert payload["type"] == "interactive"
    assert payload["interactive"]["type"] == "list"
    assert payload["interactive"]["action"]["button"] == "View"
    assert len(payload["interactive"]["action"]["sections"]) == 1


# =============================================================================
# LOCATION & REACTION TESTS
# =============================================================================


def test_render_location(base_fields):
    """Test location message rendering."""
    cmd = LocationMessage(
        **base_fields,
        latitude=37.7749,
        longitude=-122.4194,
        name="San Francisco",
        address="California, USA",
    )

    payload = render(cmd)

    assert payload["type"] == "location"
    assert payload["location"]["latitude"] == 37.7749
    assert payload["location"]["longitude"] == -122.4194
    assert payload["location"]["name"] == "San Francisco"


def test_render_reaction(base_fields):
    """Test reaction message rendering."""
    cmd = ReactionMessage(
        **base_fields,
        target_message_id="wamid.original",
        emoji="👍",
    )

    payload = render(cmd)

    assert payload["type"] == "reaction"
    assert payload["reaction"]["message_id"] == "wamid.original"
    assert payload["reaction"]["emoji"] == "👍"


def test_render_mark_as_read(base_fields):
    """Test mark as read rendering."""
    cmd = MarkAsReadMessage(
        message_id=base_fields["message_id"],
        workspace_id=base_fields["workspace_id"],
        phone_number_id=base_fields["phone_number_id"],
        target_message_id="wamid.toread",
    )

    payload = render(cmd)

    assert payload["messaging_product"] == "whatsapp"
    assert payload["status"] == "read"
    assert payload["message_id"] == "wamid.toread"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


def test_render_unknown_type_raises(base_fields):
    """Test that unknown types raise ValueError."""

    # Create a mock object that's not a known message type
    class FakeMessage:
        pass

    with pytest.raises(ValueError, match="Unknown command type"):
        render(FakeMessage())
