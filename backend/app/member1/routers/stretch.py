"""501-stub placeholders for every endpoint NOT owned by Member 1 in Phase 1:
auth (16.1, Member 2), alerts/cases/coordination (16.5, Member 2), the case
audit trail (16.6, Member 2), and every optional/stretch endpoint (16.7,
unclaimed/stretch scope). Real implementations are owned by whichever member
picks them up later — see docs/16-hour-hackathon-phase-distribution.md.

Kept in one file, registered last, so it is obvious at a glance which paths
are NOT yet real and to avoid any accidental collision with a real Member 1
route registered earlier in app/main.py.
"""
from __future__ import annotations

import inspect
import re

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1", tags=["stretch-501-stub"])

_PATH_PARAM_RE = re.compile(r"{(\w+)}")


def _make_stub_handler(path: str, owner: str, purpose: str):
    """Builds an async handler whose signature exactly matches `path`'s
    `{param}` placeholders, so FastAPI's dependant-building (which requires
    every path param to appear as a named function parameter) is satisfied
    without hand-writing one function per stub route."""
    param_names = _PATH_PARAM_RE.findall(path)
    detail = {"code": "not_implemented", "message": f"Not implemented in Phase 1 (owner={owner}): {purpose}"}

    async def handler(**kwargs: str):  # noqa: ARG001 - path params accepted but unused
        raise HTTPException(status_code=501, detail=detail)

    handler.__signature__ = inspect.Signature(
        parameters=[
            inspect.Parameter(name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
            for name in param_names
        ]
    )
    return handler


_STUB_ROUTES: list[tuple[str, str, str, str]] = [
    # method, path, owner, purpose
    ("POST", "/auth/demo-login", "Member2", "Obtain a demo JWT for a seeded role"),
    ("GET", "/me", "Member2", "Profile, roles, provider/area/outlet scopes, preferred locale"),
    ("PATCH", "/me/preferences", "Member2", "Change preferred locale only"),
    ("GET", "/alerts", "Member2", "Authorized alert list"),
    ("GET", "/alerts/{alert_id}", "Member2", "Structured source links and localized explanation"),
    ("GET", "/alerts/{alert_id}/explanations", "Member2", "Available EN/Bangla/Banglish render snapshots"),
    ("POST", "/alerts/{alert_id}/cases", "Member2", "Open a case if requires_case"),
    ("GET", "/cases", "Member2", "Authorized work queue"),
    ("GET", "/cases/{case_id}", "Member2", "Case, source alert, owner, recommended next step, status"),
    ("GET", "/cases/{case_id}/timeline", "Member2", "Evidence, assignments, statuses, notes, notification/audit history"),
    ("POST", "/cases/{case_id}/assignments", "Member2", "Assign/reassign within authorized provider boundary"),
    ("POST", "/cases/{case_id}/acknowledge", "Member2", "Legal open -> acknowledged transition"),
    ("POST", "/cases/{case_id}/escalate", "Member2", "Escalate with target role/user and reason"),
    ("POST", "/cases/{case_id}/resolve", "Member2", "Resolve with mandatory resolution summary"),
    ("POST", "/cases/{case_id}/notes", "Member2", "Add immutable case note"),
    ("POST", "/cases/{case_id}/review", "Member2", "Record benign/unusual/inconclusive/data-issue review"),
    ("GET", "/notifications", "Member2", "Caller's in-app notifications"),
    ("POST", "/notifications/{notification_id}/read", "Member2", "Mark caller's notification read"),
    ("GET", "/cases/{case_id}/audit-events", "Member2", "Authorized case audit trail"),
    ("POST", "/outlets/{outlet_id}/what-if-runs", "unclaimed-stretch", "Run a clearly labeled non-operational demand scenario"),
    ("GET", "/what-if-runs/{what_if_run_id}", "unclaimed-stretch", "Retrieve assumptions and simulated result"),
    ("GET", "/outlets/{outlet_id}/relationships", "unclaimed-stretch", "Derived synthetic relationship evidence"),
    ("GET", "/outlets/{outlet_id}/nearby-support-options", "unclaimed-stretch", "Authorized, synthetic nearby-outlet suggestions"),
    ("POST", "/cases/{case_id}/support-requests", "unclaimed-stretch", "Record a request to coordinate through an approved process"),
]

for _method, _path, _owner, _purpose in _STUB_ROUTES:
    router.add_api_route(
        _path,
        _make_stub_handler(_path, _owner, _purpose),
        methods=[_method],
        status_code=501,
        summary=f"[STUB owner={_owner}] {_purpose}",
        include_in_schema=True,
    )
