"""Job Ops UI API — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ui_api.database import init_jobs_table
from ui_api.routes.jobs import router as jobs_router
from ui_api.routes.pipeline import router as pipeline_router
from ui_api.routes.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Runs init_jobs_table() on startup so the jobs table always exists in the
    shared SQLite database before the first request is served.
    """
    logger.info("Initialising jobs table in shared SQLite database…")
    init_jobs_table()
    logger.info("Database ready.")
    yield
    logger.info("Job Ops API shutting down.")


app = FastAPI(
    title="Job Ops API",
    description="Backend API for the Job Ops job-application management UI.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js / React dev server running on localhost:3000
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(jobs_router)
app.include_router(pipeline_router)
app.include_router(chat_router)


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    """Lightweight liveness probe."""
    return {"status": "ok"}
