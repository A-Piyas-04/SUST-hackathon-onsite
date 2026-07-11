# Member 2 — Coordination & Security Contract (P1-M2, frozen)

**Owner:** Member 2 · **Status:** Phase 1 frozen; runtime unimplemented
**Package:** `backend/app/coordination/` · **Tests:** `backend/tests/coordination/` (128 passing)
**Contract version:** `coordination v0.1.0-P1`

This is the single authoritative Member 2 contract. Supporting files:
`threat-model.md`, `unresolved-dependencies.md`, `phase-2-handoff.md`,
`P1-M2-completion-report.md`.

Everything below is **contract-frozen**, not runtime-complete. Persistence, JWT
issuance, RBAC/RLS enforcement, routing execution, and workflow mutations are
later phases. Every scaffolded endpoint currently returns an honest `501
NOT_IMPLEMENTED` with the standard error body — never a fake `200`.

---

## 1. Endpoint acceptance checklist (19 MVP endpoints)

Legend — Auth: JWT required (Phase 2). Idem: requires `Idempotency-Key`. Ver:
requires `version`/`If-Match`. Phase: when runtime behaviour lands.

| Method | Route | Purpose | Auth | Scope | Idem | Ver | Safe errors | Module | Runtime phase |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/api/v1/auth/demo-login` | Issue demo session for a seeded identity | No | none | No | No | INVALID_CREDENTIALS, INACTIVE_USER, VALIDATION_ERROR | auth | P2 |
| GET | `/api/v1/me` | Profile, roles, explicit scopes, locale | Yes | self | No | No | UNAUTHENTICATED, TOKEN_* | auth/profile | P2 |
| PATCH | `/api/v1/me/preferences` | Update preferred locale ONLY | Yes | self | No | No | VALIDATION_ERROR, INVALID_LOCALE | auth/profile | P2 |
| GET | `/api/v1/alerts` | Authorized filtered alert queue | Yes | provider/outlet/area | No | No | NOT_FOUND (empty ok) | alerts | P2/P3 |
| GET | `/api/v1/alerts/{alert_id}` | Structured alert + evidence refs + case | Yes | resource | No | No | NOT_FOUND | alerts | P3 |
| GET | `/api/v1/alerts/{alert_id}/explanations` | Saved localized render snapshots | Yes | resource | No | No | NOT_FOUND | alerts | P3 |
| POST | `/api/v1/alerts/{alert_id}/cases` | Idempotently open a routed case | Yes | resource | **Yes** | No | NOT_FOUND, CANDIDATE_REJECTED | alerts | P3 |
| GET | `/api/v1/cases` | Authorized case work queue | Yes | provider/area/owner | No | No | NOT_FOUND (empty ok) | cases | P2/P4 |
| GET | `/api/v1/cases/{case_id}` | Case + alert + owner + next step + status | Yes | resource | No | No | NOT_FOUND | cases | P4 |
| GET | `/api/v1/cases/{case_id}/timeline` | Chronological history | Yes | resource | No | No | NOT_FOUND | cases | P4 |
| POST | `/api/v1/cases/{case_id}/assignments` | Assign/reassign/escalation ownership | Yes | resource | **Yes** | **Yes** | NOT_FOUND, VERSION_CONFLICT | cases | P4 |
| POST | `/api/v1/cases/{case_id}/acknowledge` | `open → acknowledged` | Yes | actor | **Yes** | **Yes** | ILLEGAL_TRANSITION, VERSION_CONFLICT | cases | P4 |
| POST | `/api/v1/cases/{case_id}/escalate` | Escalate + target/reason | Yes | actor | **Yes** | **Yes** | ILLEGAL_TRANSITION, MISSING_TRANSITION_DATA, VERSION_CONFLICT | cases | P4 |
| POST | `/api/v1/cases/{case_id}/resolve` | Resolve + mandatory summary | Yes | actor | **Yes** | **Yes** | ILLEGAL_TRANSITION, MISSING_TRANSITION_DATA, VERSION_CONFLICT | cases | P4 |
| POST | `/api/v1/cases/{case_id}/notes` | Append immutable note | Yes | resource | **Yes** | No | NOT_FOUND, UNSAFE_CONTENT | cases | P4 |
| POST | `/api/v1/cases/{case_id}/review` | Record non-fraud review | Yes | actor | **Yes** | No | NOT_FOUND, UNSAFE_CONTENT | cases | P4 |
| GET | `/api/v1/notifications` | Caller's in-app notifications | Yes | self | No | No | UNAUTHENTICATED | notifications | P4 |
| POST | `/api/v1/notifications/{notification_id}/read` | Idempotent mark-read | Yes | self | **Yes** | No | NOT_FOUND | notifications | P4 |
| GET | `/api/v1/cases/{case_id}/audit-events` | Append-only audit trail | Yes | resource | No | No | NOT_FOUND | audit (via cases) | P4 |

**Stretch (NOT in Phase 1):** `POST /api/v1/cases/{case_id}/support-requests` — deferred to post-Hour-12.
**Explicitly forbidden:** any `PATCH /api/v1/cases/{caseId}/status`; any transfer/convert/settle/refill/recover/reverse/block/freeze/accuse/fraud endpoint. Tests `test_no_generic_status_patch_endpoint` / `test_no_financial_action_endpoints` enforce this.

---

## 2. Table / migration ownership matrix

| Table / view | Owner | Purpose | Source refs | Migration file | FK owner | RLS/grant | Applied phase |
|---|---|---|---|---|---|---|---|
| `app_users` | M2 | Demo profile | — | `member_2_identity_access/001` | M2 | M2 | P2 |
| `user_access_scopes` | M2 | Provider-boundary source of truth | providers/areas/outlets (M1) | `member_2_identity_access/001` | M1 refs | M2 | P2 |
| `alerts` | M2 | Immutable analytical alert | simulation_runs, outlets, providers (M1) | `member_2_workflow/001` (slot 004) | M1 refs | M2 | P3 |
| `alert_liquidity_projections` | M2 | Typed source link | liquidity_projections (M1/M3) | `member_2_workflow/001` | M1 | M2 | P3 |
| `alert_anomaly_flags` | M2 | Typed source link | anomaly_flags (M1/M3) | `member_2_workflow/001` | M1 | M2 | P3 |
| `alert_quality_assessments` | M2 | Typed source link | data_quality_assessments (M1/M3) | `member_2_workflow/001` | M1 | M2 | P3 |
| `explanation_templates` | M2 | Versioned templates | — | `member_2_workflow/001` | M2 | M2 | P3 |
| `alert_explanations` | M2 | Immutable render snapshot | alerts | `member_2_workflow/001` | M2 | M2 | P3 |
| `routing_rules` | M2 | Routing config | providers/areas (M1) | `member_2_workflow/001` | M1 refs | M2 | P3 |
| `cases` | M2 | Mutable workflow state | alerts, outlets, providers | `member_2_workflow/001` | mixed | M2 | P3/P4 |
| `case_assignments` | M2 | Append-only ownership | cases, app_users | `member_2_workflow/001` | M2 | M2 | P4 |
| `case_status_history` | M2 | Append-only transitions | cases | `member_2_workflow/001` | M2 | M2 | P4 |
| `case_notes` | M2 | Append-only notes | cases, app_users | `member_2_workflow/001` | M2 | M2 | P4 |
| `notifications` | M2 | In-app notifications | cases, app_users | `member_2_workflow/001` | M2 | M2 | P4 |
| `case_reviews` | M2 | Non-fraud review | cases, app_users | `member_2_workflow/001` | M2 | M2 | P4 |
| `audit_events` | M2 | Strictly append-only audit | cases/alerts | `member_2_workflow/001` | M2 | M2 (append-only) | P4 |
| `v_case_timeline` | M2 | Timeline read model | many | (view, Phase 4) | M2 | M2 | P4 |
| RLS/grants/triggers | M2 | Defense in depth + immutability | all M2 tables | `member_2_workflow/002` (slot 006) | M2 | M2 | P4 |
| providers/areas/outlets/outlet_provider_accounts | **M1** | Master data | — | `001_foundation` | M1 | M1 | done |
| liquidity_projections/anomaly_flags/data_quality_assessments | **M1/M3** | Analytical source records | — | `003_intelligence` | M1 | M1 | — |

**No duplicate ownership:** Member 2 never re-creates provider/area/outlet/account/analytical-result tables; it references them by ID/contract only. See `unresolved-dependencies.md` for the identity-access numbering question sent to Member 1.

---

## 3. Role / scope matrix (`ROLE_SCOPE_MATRIX`, v1)

Code: `app/coordination/auth/policies.py`. A **missing provider scope is never a wildcard**.

| Role | Min scope | Read-only | Raw cross-provider by role | Intended behaviour |
|---|---|---|---|---|
| `agent` | outlet | no | no | Own-outlet combined alert/case view; act only when assigned/allowed |
| `field_officer` | provider + area | no | no | Assigned provider/area cases |
| `area_manager` | provider + area | no | no | Provider/area queue + authorized escalation |
| `provider_ops` | provider | no | no | Own-provider alerts/cases only |
| `risk_analyst` | provider | no | no | Escalated own-provider cases/reviews |
| `management` | explicit aggregate | **yes** | no (only if provider explicitly in scope) | Read-only aggregate; no raw cross-provider evidence by default |
| `admin` | demo/setup | yes | no | Setup only; **not** an operational shortcut |

Decision function: `evaluate_read(caller, resource) -> AccessDecision`. A denied
confidential-resource read is mapped by the service to the **same safe 404** as a
missing record (existence never disclosed).

---

## 4. Legal case-transition matrix (`state_machine.py`)

| From | Action | To | Required data |
|---|---|---|---|
| none | open | `open` | alert_id, recipient_role, current_owner_role, recommended_next_step |
| `open` | acknowledge | `acknowledged` | expected_version |
| `open` | escalate | `escalated` | target_role, reason, expected_version |
| `acknowledged` | escalate | `escalated` | target_role, reason, expected_version |
| `acknowledged` | resolve | `resolved` | resolution_summary, expected_version |
| `escalated` | resolve | `resolved` | resolution_summary, expected_version |

All other transitions rejected (`ILLEGAL_TRANSITION`). **`open → resolved` is
invalid in the MVP.** Reopening is out of scope. Enforced by `test_transitions.py`.

---

## 5. Safe error policy

Frozen shape (all Member 2 errors):

```json
{ "error": { "code": "string", "message": "string", "request_id": "string", "details": {} } }
```

Rules (enforced by `shared/errors.py` + tests):
- `request_id` always present.
- **Missing record and forbidden cross-provider lookup return the identical
  `NOT_FOUND`/404 body** (same code, message, empty details) — differing only by
  `request_id`. Never `403`-vs-`404` for the two cases.
- `details` is allowlisted + leak-scanned: no tokens, JWTs, passwords, PINs,
  OTPs, other-provider IDs, or confidential evidence.
- Error codes: see `ErrorCode` enum. HTTP status mapping in `HTTP_STATUS`.

## 6. Safe-language / prohibited-action policy

Code: `shared/security.py`. Scans **user-visible / persisted workflow content
only** (structured variables, explanations, next steps, notes, reviews) — not
documentation. Rejects (a) fraud/criminal verdicts and (b) financial-action /
punitive directives, with negation-awareness so advisory copy like "this is not
proof of fraud" passes. Fixtures are additionally scanned for phone-like strings
and secret markers.

## 7. Idempotency policy (`shared/idempotency.py`)

- Header `Idempotency-Key`, 8–200 printable non-space chars.
- Required on every mutating POST **except** `demo-login` (see `IDEMPOTENT_ENDPOINTS`).
- Key scope = (endpoint template + authenticated user). Same key + same body
  fingerprint → original result; same key + different body → `409
  IDEMPOTENCY_KEY_CONFLICT`. Concurrent duplicates never double-create.
- Durable storage is Phase 4; the request policy/validator is frozen now.

## 8. Concurrency / version policy (`shared/concurrency.py`)

- `cases.version` int, default 1, `+1` per successful mutation.
- Expected version from body `version` or `If-Match`; if both present they must
  agree. Absent → `428 VERSION_REQUIRED`.
- Stale expected version → `409 VERSION_CONFLICT`, **no mutation, no audit, no
  notification**. Re-read and retry.

## 9. Alert immutability & deduplication

- **Immutable after publication:** type, severity, provider/outlet scope, typed
  source links, structured payload, detected time, render snapshots. Only
  `state` and `supersedes_alert_id` change, and every change is audited.
  Enforced by trigger scaffold in `member_2_workflow/002_security.sql`.
- **Deduplication** (`alerts/routing.py`): stable key
  `{alert_type}:{provider|shared_cash}:{outlet}:{condition_window}`; unique
  partial index where `state='active'`. Newer duplicate supersedes older.

## 10. Review policy

`ReviewOutcome` ∈ {benign_operational, requires_follow_up, data_quality_issue,
confirmed_unusual, inconclusive}. **No fraud verdict value exists** — a fraud
determination is structurally impossible.

---

## 11. `AlertCandidate` consumer v1 (`alerts/candidate.py`)

Required fields: `candidate_version`, `alert_type` ∈ {liquidity, anomaly,
combined, data_quality}, `outlet_id`, `provider_id` (null only for shared cash),
`severity`, `source_result_ids` (typed: `{result_type, source_result_id}`),
`detected_at` (ISO UTC), `deduplication_key`, `structured_variables`,
`plausible_benign_explanation` (required for anomaly/combined), `requires_case`,
`recommended_next_step`.

Member 2 **validates and rejects**; it never recalculates confidence/anomaly
scores or re-derives suppression — alertability/suppression come from Member 1's
persisted-result lookup.

### Rejection matrix (`RejectionCode`)

| Code | Trigger |
|---|---|
| `UNSUPPORTED_CANDIDATE_VERSION` | version not in supported set |
| `INVALID_ALERT_TYPE` | alert_type not in enum |
| `INVALID_SEVERITY` | severity not in enum |
| `INVALID_TIMESTAMP` | detected_at not ISO-UTC |
| `INVALID_DEDUPLICATION_KEY` | empty dedup key |
| `INVALID_SHARED_CASH_SCOPE` | anomaly/combined with null provider |
| `MISSING_SOURCE_RESULTS` | no typed sources |
| `SOURCE_RESULT_NOT_FOUND` | untyped/blank/unknown source |
| `SOURCE_RESULT_NOT_ALERTABLE` | source `is_alertable=false` |
| `OUTLET_SCOPE_MISMATCH` | source outlet ≠ claimed |
| `PROVIDER_SCOPE_MISMATCH` | source provider ≠ claimed |
| `SOURCE_SCOPE_MISMATCH` | `source_matches_scope` false |
| `SUPPRESSED_ANOMALY` | suppressed anomaly backing anomaly/combined |
| `MISSING_BENIGN_CONTEXT` | anomaly/combined without benign explanation |
| `UNSAFE_STRUCTURED_VARIABLE` | prohibited language in variables/benign |
| `UNSAFE_RECOMMENDED_ACTION` | prohibited language in next step |
| `CONFIDENCE_OVERRIDE_ATTEMPT` | forbidden override key in variables |
| `EMPTY_HIGH_IMPACT_EVIDENCE` | high/critical alert with no evidence vars |

### Alertability rules
1. Every source is a persisted analytical result resolvable via `ReferenceLookup`.
2. `is_alertable` / `is_suppressed` are read, never recomputed.
3. A `suppressed_data_quality` anomaly can back **only** a data-quality advisory, never an anomaly/combined alert.
4. Data-quality advisories remain representable (`data_quality` alert type, `requires_case=false`).

---

## 12. Explanation variables & sections

Structured variables (subset used by templates): `situation`, `reserve_label`,
`provider_label`, `outlet_label`, `evidence_summary`, `evidence_items`,
`confidence_level`, `uncertainty_statement`, `latest_source_at`,
`plausible_benign_explanation`, `recommended_next_step`, `data_quality_warning`.

Sections (all templates): **situation, evidence, uncertainty, next_step**; plus
**benign_context** (required for anomaly/combined). Locale: preferred locale →
saved render → **English fallback**. English exists for all four alert types;
the demo `combined` alert also ships `bn` and `bn_latn`.

## 13. Routing variables & default decision table (`alerts/routing.py`)

Variables: alert_type, provider_id, area_id, outlet_id, severity, requires_case,
suggested_recipient_role, suggested_owner_role, recommended_next_step_code,
escalation_eligible, data_quality_advisory.

Resolution order: **exact provider+area → provider → area → global fallback**,
then lowest `priority`. Default table roles: provider+area high → `area_manager`;
provider high → `provider_ops`; provider default → `provider_ops`; area default →
`field_officer`; global fallback → `provider_ops`.

---

## 14. Member 1 reference/scope interface (`shared/references.py`, PROVISIONAL)

Read-only `ReferenceLookup` Protocol Member 2 depends on (Member 1 implements):
`get_provider`, `get_outlet`, `get_account`, `account_matches`,
`get_source_result`, `source_matches_scope`, plus `CallerScope`. Returns minimum
data; `None`/`False` on miss so the Member 2 service owns the safe-404 mapping.
Mockable via `InMemoryReferenceLookup`. **Pending Member 1 approval.**

## 15. Member 3 evidence requirements (`unresolved-dependencies.md` for detail)

Member 2 preserves, and never recomputes: evidence summary + ordered items,
confidence score + level, uncertainty statement, plausible benign explanation,
data-quality status, suppression status, contributing signals, latest source
time, safe analytical next-step variables. **Pending Member 3 confirmation.**
