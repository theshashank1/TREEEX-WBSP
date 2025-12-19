"""
Inspect Dead Letter Queue - scripts/inspect_dlq.py

Quick script to see what messages are failing and why.
"""

import asyncio
import json

from server.core.redis import Queue, get_redis


async def inspect_dlq():
    """Check what's in the Dead Letter Queue."""
    redis = get_redis()

    # Get DLQ length
    dlq_key = Queue.DEAD_LETTER.value
    length = await redis.llen(dlq_key)

    print(f"Dead Letter Queue: {length} messages")
    print("=" * 80)

    if length == 0:
        print("✅ DLQ is empty - no failed messages")
        return

    # Inspect last 10 messages
    messages = await redis.lrange(dlq_key, -10, -1)

    for i, msg_bytes in enumerate(messages, 1):
        msg = json.loads(msg_bytes)
        print(f"\n--- Message {i} ---")
        print(f"Error: {msg.get('error', 'Unknown')}")
        print(f"Timestamp: {msg.get('timestamp', 'Unknown')}")

        payload = msg.get("payload", {})
        print(f"Message ID: {payload.get('message_id', 'Unknown')}")
        print(f"Type: {payload.get('type', 'Unknown')}")
        print(f"To: {payload.get('to_number', 'Unknown')}")

        # Show full payload for debugging
        print(f"\nFull Payload:")
        print(json.dumps(payload, indent=2))
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(inspect_dlq())
