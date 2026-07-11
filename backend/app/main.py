"""FastAPI app composition — router registration, startup/shutdown.

Owner: Member 1 (app composition itself). Member 2's routers are registered
here too once they exist (Phase 2+); until then only the placeholder
`app/member2_stub` package exists and is NOT registered as real routes.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import engine
from app.core.logging import configure_logging
from app.member1.routers import (
    anomaly,
    dashboard,
    ingestion,
    liquidity,
    ops,
    reference,
    simulation,
    stretch,
)

configure_logging()
logger = logging.getLogger("app.main")

settings = get_settings()

app = FastAPI(
    title="Multi-Provider Agent Liquidity & Coordination Platform API",
    version="1.0.0",
    description=(
        "Decision-support / advisory API only. No endpoint here can transfer, "
        "convert, settle, refill, recover, reverse, block, freeze, or declare "
        "fraud. See docs/System-Design.md and docs/schema.md."
    ),
)

# Allow the Next.js dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting up in ENV=%s", settings.ENV)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await engine.dispose()
    logger.info("Shutdown complete; DB engine disposed")


# --- Member 1 routers ---
app.include_router(reference.router)
app.include_router(dashboard.router)
app.include_router(simulation.router)
app.include_router(ingestion.router)
app.include_router(liquidity.router)
app.include_router(anomaly.router)
app.include_router(ops.router)
app.include_router(stretch.router)

# --- Member 2 routers (Phase 2+) ---
# TODO(owner=Member2): register auth/alerts/cases/notifications/audit routers here.
