"""Member 2 — Coordination & Security package (P1-M2 scaffolding).

Owner: Member 2. This package holds the secure human-coordination half of the
platform: demo auth/profiles, immutable alerts + explanations, provider-aware
routing and cases, notifications, and append-only audit.

Phase 1 status: contracts, policy primitives, candidate consumer, explanation
templates, route/service scaffolds, migration scaffolds, fixtures, and
executable policy tests. Runtime behaviour (persistence, JWT issuance, RBAC
middleware, RLS) is intentionally NOT implemented yet — see
docs/coordination-security/P1-M2-completion-report.md.

Design rule for this package: the *core* (policies, state machine, candidate
validation, template rendering, error/idempotency/concurrency/security policy)
is pure-stdlib and importable without FastAPI, pydantic-settings, the database,
or Member 1's package, so it is independently testable. Only the `*/routes.py`
modules depend on FastAPI, and none of them import Member 1 repositories or
Member 3 formula implementations.
"""

__all__ = ["__version__"]

# Contract version for the whole Member 2 coordination surface. Bump on a
# breaking change to any frozen contract in this package.
__version__ = "0.1.0-P1"
