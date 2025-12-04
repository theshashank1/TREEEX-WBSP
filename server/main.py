from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.api import webhooks
from server.core import redis as redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.startup()
    yield
    # Shutdown
    await redis_client.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(webhooks.router)
