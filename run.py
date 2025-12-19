"""
Run FastAPI server with ngrok tunnel.

This script starts the FastAPI server with uvicorn and creates a public ngrok tunnel.
"""
import asyncio
import os
import sys

import ngrok
import uvicorn


async def main():
    """Start FastAPI server with ngrok tunnel."""
    # Ngrok authtoken and static domain
    authtoken = "2gSubOkabKZr2IWz1rKSwi6Um4z_4VMoWbki9HyVG8AXAqCgM"
    static_domain = "destined-severely-serval.ngrok-free.app"
    
    # Create a tunnel on port 8000 with static domain
    print("🔗 Creating ngrok tunnel with static domain...")
    
    try:
        # Try to use static domain first
        try:
            listener = await ngrok.forward(8000, authtoken=authtoken, domain=static_domain)
            print(f"\n✅ Ngrok tunnel created with STATIC domain!")

        except Exception as domain_error:
            if "ERR_NGROK_334" in str(domain_error) or "already online" in str(domain_error):
                print(f"\n⚠️  Static domain is already in use. Using random URL instead...")
                listener = await ngrok.forward(8000, authtoken=authtoken)
                print(f"\n✅ Ngrok tunnel created with RANDOM domain!")
            else:
                raise domain_error
        
        print(f"🌐 Public URL: {listener.url()}")
        print(f"📊 Dashboard: http://localhost:8000")
        print(f"\n🚀 Starting FastAPI server on port 8000...\n")
        
        # Run uvicorn server (this will block)
        config = uvicorn.Config(
            "server.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
