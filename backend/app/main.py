"""Application factory and lifecycle hooks."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.db.dsn import load_dotenv
from app.db.engine import create_engine, dispose_engine, set_engine
from app.db.session import init_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    setup_logging(settings.log_level)
    engine = create_engine(settings)
    set_engine(engine)
    init_session_factory()
    yield
    await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    load_dotenv()
    settings = settings or get_settings()
    app = FastAPI(
        title="Multi-Provider Agent Liquidity & Coordination Platform",
        version=settings.contract_version,
        description=(
            "Decision-support prototype API. Phase 2 foundation — business "
            "features are stubbed until later phases."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router)
    return app


def _default_app() -> FastAPI:
    """Module-level app for uvicorn; tolerates missing .env during tooling imports."""
    load_dotenv()
    os.environ.setdefault(
        "DIRECT_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5433/liquidity_platform",
    )
    return create_app()


app = _default_app()
