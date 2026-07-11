"""Aggregate API routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health
from app.api.v1 import analytics as v1_analytics
from app.api.v1 import ingestion as v1_ingestion
from app.api.v1 import reference as v1_reference
from app.api.v1 import simulation as v1_simulation
from app.api.v1 import stubs as v1_stubs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(v1_reference.router)
api_router.include_router(v1_simulation.router)
api_router.include_router(v1_ingestion.router)
api_router.include_router(v1_analytics.router)
api_router.include_router(v1_stubs.router)
