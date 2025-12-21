"""
Azure Blob Storage Service - server/services/azure_storage.py

Handles all Azure Blob Storage operations for WhatsApp media files.
Provides workspace-isolated storage with SAS token generation.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from urllib.parse import quote, unquote, urlparse

from azure.core.exceptions import AzureError
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from server.core.config import settings
from server.core.monitoring import log_event, log_exception

# ============================================================================
# FILENAME SANITIZATION
# ============================================================================


def sanitize_filename(filename: str, max_length: int = 180) -> str:
    """
    Sanitize filename for safe Azure Blob storage.

    Normalizes unicode, removes invalid characters, and ensures unique names.
    """
    if not filename:
        return f"file_{uuid.uuid4().hex[:8]}"

    # NFC normalize unicode
    filename = unicodedata.normalize("NFC", filename)

    # Split into name and extension
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        name = filename
        ext = ""

    # Replace spaces and control characters with underscores
    name = re.sub(r"[\s\x00-\x1f\x7f]+", "_", name)

    # Remove invalid characters for Azure Blob: <>:"|?*
    name = re.sub(r'[<>:"|?*]+', "", name)

    # Replace multiple underscores with single
    name = re.sub(r"_+", "_", name)

    # Strip leading/trailing underscores and dots
    name = name.strip("_.")

    # If name is empty after sanitization, generate a random one
    if not name:
        name = f"file_{uuid.uuid4().hex[:8]}"

    # Cap length while preserving extension
    ext_len = len(ext)
    max_name_len = max_length - ext_len - 1  # -1 for safety

    if len(name) > max_name_len:
        name = name[:max_name_len]
        name = name.rstrip("_.")

    return name + ext


# Cached blob service client
_blob_service_client: Optional[BlobServiceClient] = None


def get_blob_client() -> BlobServiceClient:
    """Get Azure Blob Storage client. Initializes connection on first call."""
    global _blob_service_client

    if _blob_service_client is None:
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not configured")

        _blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        log_event("azure_storage_connected", level="info")

    return _blob_service_client


async def upload_file(
    file_data: bytes,
    filename: str,
    mime_type: str,
    workspace_id: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Upload a file to Azure Blob Storage.

    Returns (blob_url, blob_name, error).
    """
    try:
        client = get_blob_client()
        container_client = client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )

        # Generate unique blob name with workspace isolation
        unique_id = uuid.uuid4().hex[:12]
        safe_filename = sanitize_filename(filename)
        blob_name = f"{workspace_id}/{unique_id}_{safe_filename}"

        # Get blob client and upload
        blob_client = container_client.get_blob_client(blob_name)

        content_settings = ContentSettings(content_type=mime_type)

        blob_client.upload_blob(
            file_data,
            overwrite=True,
            content_settings=content_settings,
        )

        blob_url = blob_client.url

        log_event(
            "azure_upload_success",
            blob_name=blob_name,
            size=len(file_data),
            mime_type=mime_type,
        )

        return blob_url, blob_name, None

    except AzureError as e:
        log_exception("azure_upload_failed", e, filename=filename)
        return None, None, f"Azure upload failed: {str(e)}"
    except RuntimeError as e:
        log_exception("azure_upload_failed", e, filename=filename)
        return None, None, str(e)
    except Exception as e:
        log_exception("azure_upload_failed", e, filename=filename)
        return None, None, f"Unexpected error during upload: {str(e)}"


async def download_file(blob_name: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Download a file from Azure Blob Storage.

    Returns (file_bytes, error).
    """
    try:
        client = get_blob_client()
        container_client = client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )
        blob_client = container_client.get_blob_client(blob_name)

        download_stream = blob_client.download_blob()
        file_data = download_stream.readall()

        log_event(
            "azure_download_success",
            blob_name=blob_name,
            size=len(file_data),
        )

        return file_data, None

    except AzureError as e:
        log_exception("azure_download_failed", e, blob_name=blob_name)
        return None, f"Azure download failed: {str(e)}"
    except RuntimeError as e:
        log_exception("azure_download_failed", e, blob_name=blob_name)
        return None, str(e)
    except Exception as e:
        log_exception("azure_download_failed", e, blob_name=blob_name)
        return None, f"Unexpected error during download: {str(e)}"


async def delete_file(blob_name: str) -> bool:
    """Delete a file from Azure Blob Storage."""
    try:
        client = get_blob_client()
        container_client = client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )
        blob_client = container_client.get_blob_client(blob_name)

        blob_client.delete_blob()

        log_event("azure_delete_success", blob_name=blob_name)

        return True

    except AzureError as e:
        log_exception("azure_delete_failed", e, blob_name=blob_name)
        return False
    except RuntimeError as e:
        log_exception("azure_delete_failed", e, blob_name=blob_name)
        return False
    except Exception as e:
        log_exception("azure_delete_failed", e, blob_name=blob_name)
        return False


def generate_sas_url(blob_name: str, expiry_minutes: int = 60) -> Optional[str]:
    """Generate a read-only SAS URL for a blob."""
    try:
        if not settings.AZURE_STORAGE_ACCOUNT_NAME:
            log_event(
                "azure_sas_failed",
                level="error",
                error="AZURE_STORAGE_ACCOUNT_NAME not configured",
            )
            return None

        if not settings.AZURE_STORAGE_ACCOUNT_KEY:
            log_event(
                "azure_sas_failed",
                level="error",
                error="AZURE_STORAGE_ACCOUNT_KEY not configured",
            )
            return None

        start_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

        sas_token = generate_blob_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=settings.AZURE_STORAGE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            start=start_time,
            expiry=expiry_time,
            version="2023-11-03",
        )

        encoded_blob_name = quote(blob_name, safe="/")

        sas_url = (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
            f"{settings.AZURE_STORAGE_CONTAINER_NAME}/{encoded_blob_name}?{sas_token}"
        )

        log_event(
            "azure_sas_generated",
            blob_name=blob_name,
            expiry_minutes=expiry_minutes,
        )

        return sas_url

    except Exception as e:
        log_exception("azure_sas_failed", e, blob_name=blob_name)
        return None


def extract_blob_name_from_url(blob_url: str) -> Optional[str]:
    """Extract blob name from a full Azure Blob Storage URL."""
    try:
        if not blob_url:
            return None

        parsed = urlparse(blob_url)
        path = parsed.path
        path = unquote(path)

        # Path format: /container_name/blob_name
        path_parts = path.strip("/").split("/", 1)

        if len(path_parts) < 2:
            log_event(
                "azure_url_parse_failed",
                level="warning",
                url=blob_url,
                error="No blob name found in path",
            )
            return None

        blob_name = path_parts[1]

        if "?" in blob_name:
            blob_name = blob_name.split("?")[0]

        return blob_name

    except Exception as e:
        log_exception("azure_url_parse_failed", e, url=blob_url)
        return None
