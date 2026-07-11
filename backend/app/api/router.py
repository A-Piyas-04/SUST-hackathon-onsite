"""Aggregate API routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health
from app.api.v1 import stubs as v1_stubs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(v1_stubs.router)
