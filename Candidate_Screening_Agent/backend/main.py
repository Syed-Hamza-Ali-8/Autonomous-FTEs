import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.database import init_db
from routers import candidates_router, approvals_router, jobs_router, applications_router
from orchestrator import run_orchestrator
from watchers.gmail_watcher import GmailApplicationWatcher
from watchers.reply_watcher import ReplyWatcher
from daily_digest import schedule_daily_digest
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Background task references
background_tasks = []
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.

    Startup:
    - Initialize database tables
    - Start orchestrator (consumes Redis queues)
    - Start Gmail application watcher
    - Start reply watcher
    - Schedule daily digest (8:00 AM)

    Shutdown:
    - Cancel all background tasks
    - Shutdown scheduler
    """
    global background_tasks, scheduler

    logger.info("Starting Candidate Screening Agent")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Start orchestrator
    orchestrator_task = asyncio.create_task(run_orchestrator())
    background_tasks.append(orchestrator_task)
    logger.info("Orchestrator started")

    # Start Gmail application watcher
    gmail_watcher = GmailApplicationWatcher()
    gmail_task = asyncio.create_task(gmail_watcher.run())
    background_tasks.append(gmail_task)
    logger.info("Gmail application watcher started")

    # Start reply watcher
    reply_watcher = ReplyWatcher()
    reply_task = asyncio.create_task(reply_watcher.run())
    background_tasks.append(reply_task)
    logger.info("Reply watcher started")

    # Schedule daily digest at 8:00 AM
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        schedule_daily_digest,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_digest",
        name="Daily Talent Digest"
    )
    scheduler.start()
    logger.info("Daily digest scheduled for 8:00 AM")

    logger.info("All background services started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Candidate Screening Agent")

    # Cancel all background tasks
    for task in background_tasks:
        task.cancel()

    # Wait for tasks to complete cancellation
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("Background tasks stopped")

    # Shutdown scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Candidate Screening Agent API",
    description="AI-powered candidate screening system with human-in-the-loop approval",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://localhost:3001",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(candidates_router, prefix="/api/candidates", tags=["candidates"])
app.include_router(approvals_router, prefix="/api/approvals", tags=["approvals"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications_router, prefix="/api/applications", tags=["applications"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Candidate Screening Agent API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "services": {
            "orchestrator": "running",
            "gmail_watcher": "running",
            "reply_watcher": "running",
            "daily_digest": "scheduled"
        }
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
