"""Versioned API stub routers — contract placeholders for Phase 3+."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.contracts.v1.responses import AlertResponse, CaseResponse, DashboardResponse
from app.core.auth import UserContext, require_authenticated
from app.core.errors import NotImplementedFeatureError

router = APIRouter(prefix="/api/v1", tags=["stubs-phase3+"])


def _raise(phase: str, feature: str) -> None:
    raise NotImplementedFeatureError(f"{feature} — implemented in Phase {phase}.")


# --- Reference / dashboard (Phase 3) ----------------------------------------
@router.get("/providers")
async def list_providers(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Provider list")


@router.get("/areas")
async def list_areas(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Area list")


@router.get("/outlets")
async def list_outlets(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Outlet list")


@router.get("/outlets/{outlet_id}")
async def get_outlet(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Outlet detail for {outlet_id}")


@router.get("/outlets/{outlet_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Dashboard for outlet {outlet_id}")


@router.get("/outlets/{outlet_id}/transactions")
async def list_transactions(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Transactions for outlet {outlet_id}")


@router.get("/outlets/{outlet_id}/balances/history")
async def balance_history(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Balance history for outlet {outlet_id}")


# --- Simulation / ingestion (Phase 3) ---------------------------------------
@router.get("/simulations/scenarios")
async def list_scenarios(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Simulation scenarios")


@router.post("/simulations/runs")
async def start_simulation(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Simulation run start")


@router.get("/simulations/runs/{run_id}")
async def get_simulation_run(
    run_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Simulation run {run_id}")


@router.post("/simulations/runs/{run_id}/reset")
async def reset_simulation_run(
    run_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Simulation reset {run_id}")


@router.post("/simulations/runs/{run_id}/faults")
async def create_fault(
    run_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Fault injection for run {run_id}")


@router.patch("/simulations/runs/{run_id}/faults/{fault_id}")
async def patch_fault(
    run_id: UUID,
    fault_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Fault toggle {fault_id} on run {run_id}")


@router.post("/ingestion/batches")
async def ingest_batch(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("3", "Ingestion batch")


@router.get("/outlets/{outlet_id}/data-quality")
async def current_data_quality(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Current data quality for outlet {outlet_id}")


@router.get("/outlets/{outlet_id}/data-quality/history")
async def data_quality_history(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("3", f"Data quality history for outlet {outlet_id}")


# --- Analytics (Phase 4) ------------------------------------------------------
@router.get("/outlets/{outlet_id}/liquidity-projections")
async def liquidity_projections(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("4", f"Liquidity projections for outlet {outlet_id}")


@router.post("/internal/analytics/liquidity/run")
async def run_liquidity_analytics(
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("4", "Liquidity analytics run")


@router.get("/outlets/{outlet_id}/anomaly-flags")
async def anomaly_flags(
    outlet_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("4", f"Anomaly flags for outlet {outlet_id}")


@router.get("/anomaly-flags/{flag_id}")
async def anomaly_flag_detail(
    flag_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("4", f"Anomaly flag {flag_id}")


@router.post("/internal/analytics/anomalies/run")
async def run_anomaly_analytics(
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("4", "Anomaly analytics run")


# --- Auth / alerts / cases (Phase 5) ----------------------------------------
@router.post("/auth/demo-login")
async def demo_login():
    _raise("5", "Demo login")


@router.get("/me")
async def current_user_profile(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", "Current user profile")


@router.patch("/me/preferences")
async def update_preferences(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", "User preferences")


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", "Alert list")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Alert {alert_id}")


@router.get("/alerts/{alert_id}/explanations")
async def alert_explanations(
    alert_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Alert explanations {alert_id}")


@router.post("/alerts/{alert_id}/cases")
async def open_case_from_alert(
    alert_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Open case from alert {alert_id}")


@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", "Case list")


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case {case_id}")


@router.get("/cases/{case_id}/timeline")
async def case_timeline(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case timeline {case_id}")


@router.post("/cases/{case_id}/assignments")
async def assign_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case assignment {case_id}")


@router.post("/cases/{case_id}/acknowledge")
async def acknowledge_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case acknowledge {case_id}")


@router.post("/cases/{case_id}/escalate")
async def escalate_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case escalate {case_id}")


@router.post("/cases/{case_id}/resolve")
async def resolve_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", f"Case resolve {case_id}")


@router.post("/cases/{case_id}/notes")
async def add_case_note(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case note {case_id}")


@router.post("/cases/{case_id}/review")
async def review_case(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case review {case_id}")


@router.get("/notifications")
async def list_notifications(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("5", "Notifications")


@router.post("/notifications/{notification_id}/read")
async def read_notification(
    notification_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Notification read {notification_id}")


@router.get("/cases/{case_id}/audit-events")
async def case_audit_events(
    case_id: UUID,
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    _raise("5", f"Case audit events {case_id}")


# --- Validation (Phase 7) -----------------------------------------------------
@router.get("/validation/results")
async def validation_results(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("7", "Validation results")
