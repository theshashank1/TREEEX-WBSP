"""
WhatsApp Business API Client for interacting with Meta's Graph API.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx

from server.core.config import settings
from server.core.monitoring import log_event, log_exception

# Default API version
DEFAULT_API_VERSION = "v21.0"

# Meta Graph API base URL
META_GRAPH_API_BASE = "https://graph.facebook.com"

# Timeout for HTTP requests (in seconds)
HTTP_TIMEOUT = 10.0


def _normalize_phone_number(phone: str) -> str:
    """
    Normalize a phone number by removing all non-digit characters except leading +.

    Args:
        phone: Phone number string (e.g., "+1 (555) 123-4567")

    Returns:
        Normalized phone number (e.g., "+15551234567")
    """
    if not phone:
        return ""
    # Preserve leading + if present, then keep only digits
    has_plus = phone.startswith("+")
    digits = re.sub(r"[^\d]", "", phone)
    return f"+{digits}" if has_plus else digits


@dataclass
class MetaAPIError:
    """Error details from Meta Graph API."""

    code: int
    message: str
    error_subcode: Optional[int] = None


@dataclass
class PhoneNumberInfo:
    """Phone number information from Meta Graph API."""

    phone_number: str
    display_phone_number: str
    verified_name: Optional[str] = None
    quality_rating: Optional[str] = None
    messaging_limit_tier: Optional[str] = None
    is_official_business_account: bool = False


class WhatsAppClient:
    """Client for interacting with Meta's Graph API for WhatsApp Business."""

    def __init__(self, access_token: str, api_version: Optional[str] = None):
        """
        Initialize WhatsApp client.

        Args:
            access_token: System User Access Token
            api_version: Meta Graph API version (e.g., "v21.0")
        """
        self.access_token = access_token
        self.api_version = api_version or settings.META_API_VERSION or DEFAULT_API_VERSION
        self.base_url = f"{META_GRAPH_API_BASE}/{self.api_version}"

    async def validate_token(self) -> tuple[bool, Optional[MetaAPIError]]:
        """
        Validate the access token with Meta API.

        Returns:
            Tuple of (is_valid, error).
            If valid and has whatsapp_business_messaging permission, returns (True, None).
            Otherwise returns (False, MetaAPIError).
        """
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(
                    f"{self.base_url}/debug_token",
                    params={
                        "input_token": self.access_token,
                        "access_token": self.access_token,
                    },
                )

                data = response.json()

                if response.status_code != 200:
                    error_data = data.get("error", {})
                    return False, MetaAPIError(
                        code=error_data.get("code", response.status_code),
                        message=error_data.get("message", "Unknown error"),
                        error_subcode=error_data.get("error_subcode"),
                    )

                token_data = data.get("data", {})

                # Check if token is valid
                if not token_data.get("is_valid", False):
                    return False, MetaAPIError(
                        code=190,
                        message="The access token is invalid or has expired.",
                    )

                # Check for whatsapp_business_messaging permission
                scopes = token_data.get("scopes", [])
                if "whatsapp_business_messaging" not in scopes:
                    return False, MetaAPIError(
                        code=10,
                        message="Token lacks required 'whatsapp_business_messaging' permission.",
                    )

                log_event(
                    "token_validated",
                    level="debug",
                    app_id=token_data.get("app_id"),
                    scopes=",".join(scopes),
                )
                return True, None

        except httpx.TimeoutException:
            log_exception("Token validation timed out")
            return False, MetaAPIError(
                code=-1,
                message="Request to Meta API timed out.",
            )
        except Exception as e:
            log_exception("Token validation failed", e)
            return False, MetaAPIError(
                code=-1,
                message=f"Failed to validate token: {str(e)}",
            )

    async def get_phone_number(
        self, phone_number_id: str
    ) -> tuple[Optional[PhoneNumberInfo], Optional[MetaAPIError]]:
        """
        Fetch phone number details from Meta Graph API.

        Args:
            phone_number_id: Meta's Phone Number ID

        Returns:
            Tuple of (PhoneNumberInfo, None) on success,
            or (None, MetaAPIError) on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(
                    f"{self.base_url}/{phone_number_id}",
                    params={
                        "access_token": self.access_token,
                        "fields": "display_phone_number,verified_name,quality_rating,messaging_limit_tier,is_official_business_account",
                    },
                )

                data = response.json()

                if response.status_code != 200:
                    error_data = data.get("error", {})
                    return None, MetaAPIError(
                        code=error_data.get("code", response.status_code),
                        message=error_data.get("message", "Unknown error"),
                        error_subcode=error_data.get("error_subcode"),
                    )

                phone_info = PhoneNumberInfo(
                    phone_number=_normalize_phone_number(data.get("display_phone_number", "")),
                    display_phone_number=data.get("display_phone_number", ""),
                    verified_name=data.get("verified_name"),
                    quality_rating=data.get("quality_rating"),
                    messaging_limit_tier=data.get("messaging_limit_tier"),
                    is_official_business_account=data.get("is_official_business_account", False),
                )

                log_event(
                    "phone_number_fetched",
                    level="debug",
                    phone_number_id=phone_number_id,
                    quality_rating=phone_info.quality_rating,
                )
                return phone_info, None

        except httpx.TimeoutException:
            log_exception("Phone number fetch timed out", phone_number_id=phone_number_id)
            return None, MetaAPIError(
                code=-1,
                message="Request to Meta API timed out.",
            )
        except Exception as e:
            log_exception("Phone number fetch failed", e, phone_number_id=phone_number_id)
            return None, MetaAPIError(
                code=-1,
                message=f"Failed to fetch phone number: {str(e)}",
            )

    @staticmethod
    def parse_message_limit(tier: Optional[str]) -> int:
        """
        Convert messaging limit tier to message count.

        Args:
            tier: Messaging limit tier string (e.g., "TIER_1K")

        Returns:
            Message limit as integer
        """
        tier_mapping = {
            "TIER_50": 50,
            "TIER_250": 250,
            "TIER_1K": 1000,
            "TIER_10K": 10000,
            "TIER_100K": 100000,
            "TIER_UNLIMITED": 999999999,
        }
        return tier_mapping.get(tier, 1000)
