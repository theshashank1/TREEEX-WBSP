"""
Media Download Worker - server/workers/media.py

Downloads WhatsApp media from Meta CDN and stores in Azure Blob Storage.
Processes jobs from MEDIA_DOWNLOAD queue.

ARCHITECTURE:
    - Pulls events from Redis queue (MEDIA_DOWNLOAD)
    - Fetches access token from PhoneNumber record
    - Downloads media from WhatsApp using WhatsAppClient
    - Uploads to Azure Blob Storage
    - Updates MediaFile record with storage_url
    - Moves failed jobs to Dead Letter Queue after max retries

RUNNING:
    python -m server.workers.media

    Or with multiple workers:
    python -m server.workers.media --workers 2
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select

from server.core.db import async_session_maker as async_session
from server.core.db import engine
from server.core.monitoring import log_event, log_exception
from server.core.redis import Queue, dequeue, enqueue, move_to_dlq
from server.core.redis import shutdown as redis_shutdown
from server.core.redis import startup as redis_startup
from server.models.contacts import PhoneNumber
from server.models.messaging import MediaFile
from server.services import azure_storage
from server.whatsapp.client import WhatsAppClient

# ============================================================================
# WORKER STATE
# ============================================================================


class WorkerState:
    running: bool = True

    @classmethod
    def shutdown(cls):
        cls.running = False
        log_event("media_worker_shutdown_signal")


# ============================================================================
# JOB HANDLER
# ============================================================================


async def process_media_job(job: Dict[str, Any]) -> bool:
    """
    Process a single media download job.

    Downloads media from WhatsApp, uploads to Azure, and updates DB.
    """
    media_id = job.get("media_id")
    workspace_id = job.get("workspace_id")
    wa_media_id = job.get("wa_media_id")
    mime_type = job.get("mime_type", "application/octet-stream")
    phone_number_id_meta = job.get("phone_number_id")

    if not all([media_id, workspace_id, wa_media_id, phone_number_id_meta]):
        log_event(
            "media_job_missing_fields",
            level="warning",
            job=job,
        )
        return False

    async with async_session() as session:
        try:
            result = await session.execute(
                select(MediaFile).where(MediaFile.id == UUID(media_id))
            )
            media = result.scalar_one_or_none()

            if not media:
                log_event(
                    "media_job_media_not_found",
                    level="warning",
                    media_id=media_id,
                )
                return False

            if media.storage_url:
                log_event(
                    "media_job_already_processed",
                    level="debug",
                    media_id=media_id,
                )
                return True

            result = await session.execute(
                select(PhoneNumber).where(
                    PhoneNumber.phone_number_id == phone_number_id_meta
                )
            )
            phone_number = result.scalar_one_or_none()

            if not phone_number:
                log_event(
                    "media_job_phone_not_found",
                    level="warning",
                    phone_number_id=phone_number_id_meta,
                )
                return False

            client = WhatsAppClient(access_token=phone_number.access_token)
            file_bytes, downloaded_mime_type, error = await client.download_media(
                media_id=wa_media_id,
                phone_number_id=phone_number_id_meta,
            )

            if error:
                log_event(
                    "media_job_download_failed",
                    level="error",
                    media_id=media_id,
                    wa_media_id=wa_media_id,
                    error_code=error.code,
                    error_message=error.message,
                )
                return False

            if not file_bytes:
                log_event(
                    "media_job_empty_download",
                    level="warning",
                    media_id=media_id,
                    wa_media_id=wa_media_id,
                )
                return False

            # Use downloaded MIME type if available, otherwise use from job
            final_mime_type = downloaded_mime_type or mime_type

            filename = media.file_name or f"{media.type}_{wa_media_id}"
            blob_url, blob_name, upload_error = await azure_storage.upload_file(
                file_data=file_bytes,
                filename=filename,
                mime_type=final_mime_type,
                workspace_id=workspace_id,
            )

            if upload_error:
                log_event(
                    "media_job_upload_failed",
                    level="error",
                    media_id=media_id,
                    error=upload_error,
                )
                return False

            media.storage_url = blob_url
            media.file_size = len(file_bytes)
            media.mime_type = final_mime_type

            await session.commit()

            log_event(
                "media_job_processed",
                media_id=media_id,
                workspace_id=workspace_id,
                file_size=len(file_bytes),
                blob_name=blob_name,
            )

            return True

        except Exception as e:
            log_exception("media_job_error", e, media_id=media_id)
            await session.rollback()
            return False


# ============================================================================
# WORKER LOOP
# ============================================================================


async def worker_loop(worker_id: int = 0) -> None:
    """Main worker loop."""
    log_event("media_worker_started", worker_id=worker_id)

    retry_counts: Dict[str, int] = {}
    max_retries = 3

    while WorkerState.running:
        job = None

        try:
            job = await dequeue(Queue.MEDIA_DOWNLOAD, timeout=5)

            if not job:
                await asyncio.sleep(0.1)
                continue

            job_id = job.get("media_id", "unknown")

            success = await process_media_job(job)

            if not success:
                retry_key = f"media:{job_id}"
                retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1

                if retry_counts[retry_key] < max_retries:
                    log_event(
                        "media_worker_job_retry",
                        level="warning",
                        job_id=job_id,
                        attempt=retry_counts[retry_key],
                    )
                    job["_retry_count"] = retry_counts[retry_key]
                    await asyncio.sleep(2 ** retry_counts[retry_key])  # Backoff
                    await enqueue(Queue.MEDIA_DOWNLOAD, job)
                else:
                    log_event(
                        "media_worker_job_to_dlq",
                        level="error",
                        job_id=job_id,
                    )
                    await move_to_dlq(
                        Queue.MEDIA_DOWNLOAD,
                        job,
                        "Max retries exceeded",
                    )
                    del retry_counts[retry_key]
            else:
                retry_key = f"media:{job_id}"
                if retry_key in retry_counts:
                    del retry_counts[retry_key]

        except Exception as e:
            log_exception("media_worker_loop_error", e, worker_id=worker_id)
            await asyncio.sleep(1)

    log_event("media_worker_stopped", worker_id=worker_id)


async def run_workers(num_workers: int = 1) -> None:
    """Run multiple worker instances concurrently."""

    await redis_startup()

    log_event("media_workers_starting", num_workers=num_workers)

    workers = [
        asyncio.create_task(worker_loop(worker_id=i)) for i in range(num_workers)
    ]

    try:
        await asyncio.gather(*workers)
    except asyncio.CancelledError:
        log_event("media_workers_cancelled")
    finally:
        await redis_shutdown()
        if engine:
            await engine.dispose()
        log_event("media_workers_cleanup_complete")


# ============================================================================
# ENTRY POINT
# ============================================================================


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Media Download Worker")
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker instances (default: 1)",
    )
    args = parser.parse_args()

    def signal_handler(sig, frame):
        log_event("media_worker_shutdown_signal_received", signal=sig)
        WorkerState.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(run_workers(num_workers=args.workers))
    except KeyboardInterrupt:
        log_event("media_worker_keyboard_interrupt")

    log_event("media_worker_exit")
    sys.exit(0)


if __name__ == "__main__":
    main()
