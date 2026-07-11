"""Versioned API stub router — placeholder for post-MVP stretch endpoints.

Phase 3 (reference/ledger), Phase 4 (analytics), Phase 5 (auth/alerts/cases/
notifications/audit), and Phase 7 (validation/observability) are implemented in
their own routers. The Phase 7 validation-results stub has been replaced by the
persistence-backed router in ``app.api.v1.validation``.

This router intentionally exposes no routes: the five stretch endpoints
(what-if-runs, relationships, nearby-support-options, support-requests) are
gated behind the complete MVP and remain unimplemented (Phase 8+).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["stubs-phase8+"])
