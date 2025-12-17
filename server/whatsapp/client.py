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

    async def exchange_token_for_long_term(
        self,
    ) -> tuple[Optional[str], Optional[MetaAPIError]]:
        """
        Exchange a short-lived access token for a long-lived access token.
        
        Meta provides an endpoint to exchange short-lived tokens (typically 1 hour)
        for long-lived tokens (typically 60 days).
        
        Returns:
            Tuple of (long_lived_token, None) on success,
            or (None, MetaAPIError) on failure.
            
        Note: This requires the current token to be a valid short-lived user access token.
        System user tokens are already long-lived and don't need exchange.
        """
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.get(
                    f"{META_GRAPH_API_BASE}/oauth/access_token",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": settings.META_APP_ID if hasattr(settings, 'META_APP_ID') else "",
                        "client_secret": settings.META_APP_SECRET,
                        "fb_exchange_token": self.access_token,
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

                long_lived_token = data.get("access_token")
                if not long_lived_token:
                    return None, MetaAPIError(
                        code=-1,
                        message="No access token returned from exchange",
                    )

                expires_in = data.get("expires_in", 0)
                token_type = data.get("token_type", "bearer")

                log_event(
                    "token_exchanged_for_long_term",
                    level="info",
                    expires_in=expires_in,
                    token_type=token_type,
                )

                return long_lived_token, None

        except httpx.TimeoutException:
            log_exception("Token exchange timed out")
            return None, MetaAPIError(
                code=-1,
                message="Request to Meta API timed out.",
            )
        except Exception as e:
            log_exception("Token exchange failed", e)
            return None, MetaAPIError(
                code=-1,
                message=f"Failed to exchange token: {str(e)}",
            )

    async def download_media(
        self,
        media_id: str,
        phone_number_id: str,
    ) -> tuple[Optional[bytes], Optional[str], Optional[MetaAPIError]]:
        """
        Download media file from WhatsApp.

        Two-step process:
        1. GET /{api_version}/{media_id} with access token
           Response: {"url": "https://...", "mime_type": "...", "file_size": 123}
        2. Download file from URL with Authorization: Bearer {token}

        Args:
            media_id: Meta's media ID (from webhook payload)
            phone_number_id: Meta's phone number ID (for logging)

        Returns:
            Tuple of (file_bytes, mime_type, error).
            On success: (bytes, mime_type_string, None)
            On failure: (None, None, MetaAPIError)
        """
        try:
            # Longer timeout for media downloads (larger files)
            media_timeout = 60.0

            async with httpx.AsyncClient(timeout=media_timeout) as client:
                # Step 1: Get media URL from Meta Graph API
                log_event(
                    "whatsapp_media_url_fetch_start",
                    level="debug",
                    media_id=media_id,
                )

                url_response = await client.get(
                    f"{self.base_url}/{media_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )

                if url_response.status_code != 200:
                    try:
                        error_data = url_response.json().get("error", {})
                    except Exception:
                        error_data = {}

                    log_event(
                        "whatsapp_media_url_fetch_failed",
                        level="error",
                        media_id=media_id,
                        status_code=url_response.status_code,
                    )

                    return None, None, MetaAPIError(
                        code=error_data.get("code", url_response.status_code),
                        message=error_data.get("message", "Failed to get media URL"),
                        error_subcode=error_data.get("error_subcode"),
                    )

                url_data = url_response.json()
                download_url = url_data.get("url")
                mime_type = url_data.get("mime_type")
                file_size = url_data.get("file_size")

                if not download_url:
                    log_event(
                        "whatsapp_media_no_url",
                        level="error",
                        media_id=media_id,
                    )
                    return None, None, MetaAPIError(
                        code=-1,
                        message="No download URL in response",
                    )

                log_event(
                    "whatsapp_media_url_fetched",
                    level="debug",
                    media_id=media_id,
                    mime_type=mime_type,
                    file_size=file_size,
                )

                # Step 2: Download actual file from CDN URL
                download_response = await client.get(
                    download_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )

                if download_response.status_code != 200:
                    log_event(
                        "whatsapp_media_download_failed",
                        level="error",
                        media_id=media_id,
                        status_code=download_response.status_code,
                    )
                    return None, None, MetaAPIError(
                        code=download_response.status_code,
                        message=f"Failed to download media: HTTP {download_response.status_code}",
                    )

                file_bytes = download_response.content

                log_event(
                    "whatsapp_media_downloaded",
                    media_id=media_id,
                    size=len(file_bytes),
                    mime_type=mime_type,
                )

                return file_bytes, mime_type, None

        except httpx.TimeoutException:
            log_exception(
                "whatsapp_media_download_timeout",
                media_id=media_id,
            )
            return None, None, MetaAPIError(
                code=-1,
                message="Request to Meta API timed out during media download.",
            )
        except Exception as e:
            log_exception(
                "whatsapp_media_download_error",
                e,
                media_id=media_id,
            )
            return None, None, MetaAPIError(
                code=-1,
                message=f"Failed to download media: {str(e)}",
            )
