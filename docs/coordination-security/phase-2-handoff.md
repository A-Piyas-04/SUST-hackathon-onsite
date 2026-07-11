# Member 2 — Phase 2 Handoff Notes

## What Phase 2 starts from (P1-M2 artifacts)

- **Package:** `backend/app/coordination/` (imports cleanly; 128 tests pass).
- **Composition:** `app.coordination.router.include_member2_routers(app)`.
- **Frozen contracts:** `docs/coordination-security/coordination-security-contract.md`.
- **Fixtures:** `backend/fixtures/coordination/` (references, candidates
  valid/invalid, auth users, case lifecycle, safe errors).
- **Migration scaffolds (unapplied):** `backend/migrations/member_2_identity_access/`,
  `backend/migrations/member_2_workflow/`.

## Phase 2 objectives (02:15–05:00 → `P2-M2`)

1. Promote + apply `member_2_identity_access/001_identity_access.sql` (after
   resolving numbering with Member 1). Seed the 10 demo identities in
   `fixtures/coordination/auth/users.json`.
2. Implement real `AuthService` (demo login → scoped session, `/me`, locale
   preference) replacing `ScaffoldAuthService`.
3. Implement scope middleware/dependency that resolves `CallerScope` from
   `user_access_scopes` via Member 1's lookup, and enforces `evaluate_read` on
   both Member 1 and Member 2 routes.
4. Wire the safe-404 mapping: missing + forbidden cross-provider → identical
   `NOT_FOUND` body.
5. Apply alert/case skeleton migrations for empty authorized queues.
6. Add route-level Provider A / Provider B denial tests (extend
   `test_scope_policy.py` into integration tests).

## Reusable Phase-1 primitives (no rework needed)

| Need | Use |
|---|---|
| Role/scope decisions | `auth/policies.evaluate_read`, `has_minimum_scope` |
| Legal transitions | `cases/state_machine.evaluate_transition` |
| Candidate validation | `alerts/candidate.validate_candidate` |
| Safe errors / 404 | `shared/errors` (`not_found`, `ApiError`) |
| Idempotency policy | `shared/idempotency` |
| Version/concurrency | `shared/concurrency` |
| Safe language | `shared/security` |
| Explanation rendering | `alerts/templates.render` |
| Routing/dedup | `alerts/routing` |
| Member 1 lookup seam | `shared/references.ReferenceLookup` (+ `InMemoryReferenceLookup`) |

## Exit criteria carried forward (must hold from Phase 2 on)

- No application table stores credentials/password hashes/tokens.
- A provider scope is never interpreted as all providers.
- Unauthorized and missing objects are externally indistinguishable.

## Fallback if behind schedule (per plan §12)

Keep: demo login, `/me`, provider scope model, alert/case core route scaffolds,
`AlertCandidate` consumer, legal transition state machine, safe error policy,
idempotency + concurrency policy, EN + one Bangla/Banglish template, audit-event
contract, provider-boundary tests, safe-language tests. Cut first: stretch
support-request, extra review sophistication, extra routing variants, extra
localized alert types, UI polish, doc duplication. **Never** cut provider
boundaries, candidate source validation, suppressed-anomaly rejection, immutable
evidence, legal transitions, receiver/owner/next-step fields, audit,
idempotency/concurrency, safe wording, human-review boundary.
