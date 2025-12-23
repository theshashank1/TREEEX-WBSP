"""
Campaign Execution Worker - server/workers/campaign.py

Production-ready worker that processes campaign jobs from Redis queue.
Orchestrates bulk message sending with rate limiting and proper tracking.

RUNNING:
    python -m server.workers.campaign

    Or with environment:
    uv run python -m server.workers.campaign
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from server.core.config import settings
from server.core.db import async_session_maker as async_session
from server.core.db import engine
from server.core.monitoring import log_event, log_exception
from server.core.redis import Queue, dequeue, enqueue
from server.core.redis import shutdown as redis_shutdown
from server.core.redis import startup as redis_startup
from server.models.base import CampaignStatus, MessageStatus
from server.models.contacts import PhoneNumber
from server.models.marketing import Campaign, CampaignMessage

# =============================================================================
# CONFIGURATION
# =============================================================================

CAMPAIGN_RATE_LIMIT = 15  # Messages per second per campaign
CHUNK_SIZE = 100  # Messages to process per batch


# =============================================================================
# WORKER STATE
# =============================================================================


class WorkerState:
    running: bool = True

    @classmethod
    def shutdown(cls):
        cls.running = False
        log_event("campaign_worker_shutdown_signal")


# =============================================================================
# CAMPAIGN EXECUTION
# =============================================================================


async def process_campaign_job(job_data: dict) -> bool:
    """
    Process a single campaign execution job.

    Flow:
    1. Fetch campaign with template
    2. Validate campaign can be executed
    3. Fetch phone number Meta ID
    4. Iterate PENDING messages in chunks
    5. Enqueue to OUTBOUND_MESSAGES with proper payload
    6. Mark as QUEUED to prevent re-processing
    7. Update campaign status to DISPATCHED when complete
    """
    campaign_id = job_data.get("campaign_id")
    if not campaign_id:
        log_event("campaign_job_missing_id", level="error")
        return False

    async with async_session() as session:
        # 1. Fetch campaign with template
        result = await session.execute(
            select(Campaign)
            .options(joinedload(Campaign.template))
            .where(Campaign.id == UUID(campaign_id))
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            log_event("campaign_not_found", campaign_id=campaign_id)
            return False

        # 2. Validate status
        if campaign.status != CampaignStatus.RUNNING.value:
            log_event(
                "campaign_invalid_status",
                campaign_id=campaign_id,
                status=campaign.status,
            )
            return False

        if not campaign.template:
            log_event("campaign_no_template", campaign_id=campaign_id, level="error")
            campaign.status = CampaignStatus.DRAFT.value
            await session.commit()
            return False

        # 3. Fetch phone number to get Meta ID
        phone_result = await session.execute(
            select(PhoneNumber).where(
                PhoneNumber.id == campaign.phone_number_id,
                PhoneNumber.deleted_at.is_(None),
            )
        )
        phone_number = phone_result.scalar_one_or_none()

        if not phone_number:
            log_event(
                "campaign_phone_not_found",
                campaign_id=campaign_id,
                phone_number_id=str(campaign.phone_number_id),
                level="error",
            )
            campaign.status = CampaignStatus.DRAFT.value
            await session.commit()
            return False

        meta_phone_number_id = phone_number.phone_number_id  # Meta's ID

        # 4. Mark campaign start time
        if not campaign.started_at:
            campaign.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await session.commit()

        # 5. Dispatch loop - process in chunks
        dispatched_count = 0

        while WorkerState.running:
            # Refresh campaign to check for pause/cancel
            await session.refresh(campaign)
            if campaign.status != CampaignStatus.RUNNING.value:
                log_event(
                    "campaign_stopped_mid_execution",
                    campaign_id=campaign_id,
                    status=campaign.status,
                )
                break

            # Fetch next batch of PENDING messages
            result = await session.execute(
                select(CampaignMessage)
                .options(joinedload(CampaignMessage.contact))
                .where(
                    CampaignMessage.campaign_id == campaign.id,
                    CampaignMessage.status == MessageStatus.PENDING.value,
                )
                .limit(CHUNK_SIZE)
            )
            messages = result.scalars().all()

            if not messages:
                # No more pending messages -> Campaign Dispatched
                campaign.status = CampaignStatus.DISPATCHED.value
                campaign.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await session.commit()
                log_event(
                    "campaign_dispatched",
                    campaign_id=campaign_id,
                    total_dispatched=dispatched_count,
                )
                break

            # Process each message in chunk
            for msg in messages:
                if not WorkerState.running:
                    break

                # Skip if contact has no phone number
                if not msg.contact or not msg.contact.phone_number:
                    msg.status = MessageStatus.FAILED.value
                    msg.error_message = "Contact has no phone number"
                    continue

                # Build outbound message job
                message_job = {
                    "type": "template_message",
                    "message_id": str(uuid4()),  # Unique ID for outbound worker
                    "workspace_id": str(campaign.workspace_id),
                    "phone_number_id": meta_phone_number_id,  # Meta's ID
                    "to_number": msg.contact.phone_number,
                    "template_name": campaign.template.name,
                    "language_code": campaign.template.language,
                    "components": campaign.template.components,
                    # Campaign tracking
                    "is_campaign": True,
                    "campaign_message_id": str(msg.id),
                }

                # Enqueue to outbound worker
                success = await enqueue(Queue.OUTBOUND_MESSAGES, message_job)
                if success:
                    msg.status = MessageStatus.QUEUED.value
                    dispatched_count += 1
                else:
                    log_event(
                        "campaign_enqueue_failed",
                        campaign_message_id=str(msg.id),
                        level="error",
                    )
                    msg.status = MessageStatus.FAILED.value
                    msg.error_message = "Failed to enqueue message"

                # Rate limiting
                await asyncio.sleep(1.0 / CAMPAIGN_RATE_LIMIT)

            # Commit chunk progress
            await session.commit()

    return True


# =============================================================================
# WORKER LOOP
# =============================================================================


async def worker_loop(worker_id: int = 0) -> None:
    """Main worker loop."""
    log_event("campaign_worker_started", worker_id=worker_id)

    while WorkerState.running:
        try:
            job = await dequeue(Queue.CAMPAIGN_JOBS, timeout=5)

            if job:
                campaign_id = job.get("campaign_id", "unknown")
                log_event("campaign_job_received", campaign_id=campaign_id)

                try:
                    await process_campaign_job(job)
                except Exception as e:
                    log_exception("campaign_job_failed", e, campaign_id=campaign_id)
            else:
                # No jobs, idle
                await asyncio.sleep(1)

        except Exception as e:
            log_exception("campaign_worker_loop_error", e)
            await asyncio.sleep(5)

    log_event("campaign_worker_stopped", worker_id=worker_id)


async def run_worker() -> None:
    """Initialize and run campaign worker."""
    await redis_startup()
    log_event("campaign_worker_initializing")

    try:
        await worker_loop()
    except asyncio.CancelledError:
        log_event("campaign_worker_cancelled")
    finally:
        await redis_shutdown()
        await engine.dispose()
        log_event("campaign_worker_cleanup_complete")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Campaign Execution Worker")
    parser.parse_args()

    # Setup signal handlers
    def signal_handler(sig, frame):
        log_event("campaign_worker_signal", signal=sig)
        WorkerState.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 Campaign Worker Starting...")

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\n⛔ Campaign Worker interrupted")

    print("✅ Campaign Worker stopped")


if __name__ == "__main__":
    main()
