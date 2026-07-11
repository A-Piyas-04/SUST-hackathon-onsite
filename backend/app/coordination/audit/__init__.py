"""Audit module — append-only audit-event contract + read service.

The audit READ endpoint (GET /api/v1/cases/{caseId}/audit-events) is registered
by the cases router; this module owns the audit-event contract and the write
semantics that later phases must honour (append-only, same-transaction writes).
"""
