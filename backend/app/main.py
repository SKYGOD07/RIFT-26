"""
FastAPI application entry point.
Initializes database, Algorand service, and chain subscriber on startup.
"""

import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import router
from app.algorand_service import algorand_service
from app.subscriber import chain_subscriber
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Background task reference
_subscriber_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global _subscriber_task

    # ── Startup ──
    logger.info("Starting EventTicketing Backend...")

    # 1. Initialize database tables
    await init_db()
    logger.info("Database initialized.")

    # 2. Initialize Algorand service
    algorand_service.initialize()

    # 3. Start chain subscriber in background
    chain_subscriber.initialize()
    _subscriber_task = asyncio.create_task(chain_subscriber.start())
    logger.info("Chain subscriber started in background.")

    logger.info(f"Backend ready → http://{settings.host}:{settings.port}")
    logger.info(f"Swagger docs → http://{settings.host}:{settings.port}/docs")

    yield  # App is running

    # ── Shutdown ──
    logger.info("Shutting down...")
    chain_subscriber.stop()
    if _subscriber_task:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete.")


# ── App ──
app = FastAPI(
    title="EventTicketing API",
    description=(
        "Backend for the EventTicketing dApp on Algorand. "
        "Mints ticket NFTs, tracks ownership, and syncs with the blockchain."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
