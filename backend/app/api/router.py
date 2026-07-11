"""Aggregate API routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health
from app.api.v1 import alerts as v1_alerts
from app.api.v1 import analytics as v1_analytics
from app.api.v1 import auth as v1_auth
from app.api.v1 import cases as v1_cases
from app.api.v1 import ingestion as v1_ingestion
from app.api.v1 import notifications as v1_notifications
from app.api.v1 import observability as v1_observability
from app.api.v1 import reference as v1_reference
from app.api.v1 import simulation as v1_simulation
from app.api.v1 import stubs as v1_stubs
from app.api.v1 import validation as v1_validation

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(v1_observability.router)
api_router.include_router(v1_auth.router)
api_router.include_router(v1_reference.router)
api_router.include_router(v1_simulation.router)
api_router.include_router(v1_ingestion.router)
api_router.include_router(v1_analytics.router)
api_router.include_router(v1_alerts.router)
api_router.include_router(v1_cases.router)
api_router.include_router(v1_notifications.router)
api_router.include_router(v1_validation.router)
api_router.include_router(v1_stubs.router)
