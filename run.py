"""
Run FastAPI server with ngrok tunnel and auto-reload.
"""

import asyncio
import os
import sys
import threading
import time
from typing import Optional

import ngrok
import uvicorn

from server.core.config import settings

# Global event to signal ngrok is ready
ngrok_ready = threading.Event()
public_url: Optional[str] = None


async def start_ngrok():
    """Start ngrok tunnel in a separate loop."""
    global public_url

    authtoken = settings.NGROK_AUTHTOKEN
    static_domain = settings.NGROK_DOMAIN

    if not authtoken:
        print("❌ Error: NGROK_AUTHTOKEN environment variable is required")
        sys.exit(1)

    print("🔗 Creating ngrok tunnel...")

    try:
        # Try static domain first
        try:
            listener = await ngrok.forward(
                8000, authtoken=authtoken, domain=static_domain
            )
            print(f"\n✅ Ngrok tunnel created with STATIC domain!")
        except Exception:
            # Fallback to random
            print(f"\n⚠️  Static domain unavailable. Using random URL...")
            listener = await ngrok.forward(8000, authtoken=authtoken)
            print(f"\n✅ Ngrok tunnel created with RANDOM domain!")

        public_url = listener.url()
        print(f"🌐 Public URL: {public_url}")
        print(f"📊 Dashboard: http://localhost:8000")

        # Signal ready
        ngrok_ready.set()

        # Keep alive until main thread exits
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            print("🔌 Closing ngrok tunnel...")
            await listener.close()

    except Exception as e:
        print(f"\n❌ Ngrok Error: {e}")
        # Signal ready even on error so main doesn't hang (but we exit)
        ngrok_ready.set()
        sys.exit(1)


def run_ngrok_thread():
    """Thread target to run asyncio loop for ngrok."""
    try:
        asyncio.run(start_ngrok())
    except KeyboardInterrupt:
        pass


def main():
    """Main entry point."""
    print("🚀 Starting Development Server...")

    # Start ngrok in background thread
    t = threading.Thread(target=run_ngrok_thread, daemon=True)
    t.start()

    # Wait for ngrok to initialize (optional, just for better log order)
    ngrok_ready.wait(timeout=10)

    if not public_url:
        print("⚠️  Warning: Ngrok did not start in time. Starting server anyway...")

    print("\n🚀 Starting Uvicorn with Auto-Reload...\n")

    # Run uvicorn in main thread
    # reload=True ensures the server restarts on code changes
    # The ngrok tunnel (in background thread) stays alive!
    try:
        uvicorn.run(
            "server.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")


if __name__ == "__main__":
    main()
