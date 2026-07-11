# Member 2 Detailed Task Plan — Coordination & Security APIs

## 1. Mission

You own the secure human-coordination half of the product. Your work turns Member 1's validated analytical result into an immutable, explainable alert and—when important—a provider-scoped case that can be assigned, acknowledged, escalated, documented, notified, audited, reviewed, and resolved.

```text
Member 3 analytical evidence
        ↓ ResultEnvelope
Member 1 persists result and creates AlertCandidate
        ↓
You validate + deduplicate + persist immutable alert
        ↓
Explain + route + optionally open case
        ↓
Assign → acknowledge → escalate/note → resolve/review
        ↓
Notification + append-only audit + provider-boundary proof
```

Your API must support a safe human decision process. It must never recalculate analytics, expose another provider's confidential evidence, declare fraud, block/freeze an account, or execute a financial action.

## 2. Non-negotiable outcomes

By Hour 16, your owned work must prove:

1. Demo users authenticate and receive explicit role/provider/area/outlet scopes.
2. Cross-provider lookups do not reveal whether a confidential record exists.
3. Analytical alerts are immutable evidence records after publication.
4. Every high-impact alert has situation, evidence, uncertainty, safe next step, and English rendering; the demo alert also has Bangla or Banglish rendering.
5. Important alerts route to a recipient and open a case with an owner and recommended next step.
6. Only legal case transitions are accepted.
7. Assignment, acknowledgement, escalation, notes, notification, review, and resolution are traceable.
8. Duplicate POSTs do not duplicate cases/transitions/notes/notifications.
9. Concurrent/stale case updates fail safely.
10. Provider A operations cannot read or mutate Provider B alerts, cases, notes, evidence, notifications, or audit events.
11. The minimal case console demonstrates Scenario D without direct database edits.
12. Workflow and security evidence is measured and documented honestly.

## 3. Ownership boundaries

### You own

- Application profiles, roles, and access scopes.
- Demo authentication and current-user/profile APIs.
- Provider/outlet/area scope middleware and authorization policy.
- Alert persistence, typed source links, lifecycle state, and deduplication.
- Versioned EN/Bangla/Banglish explanation templates and immutable render snapshots.
- Routing rules and initial case creation.
- Case assignment, owner, status transitions, notes, review, and resolution.
- In-app notifications.
- Case timeline and append-only audit events.
- Idempotency, optimistic concurrency, safe errors, RBAC, grants, and RLS for your tables/routes.
- Minimal alert list/detail and case workflow controls.
- Workflow/security tests, reliability metrics, responsible-design documentation, and Scenario D presentation.

### You do not own

- Provider/outlet master data, ingestion, balances, transactions, dashboard, quality, forecast, anomaly, validation, health, or metrics endpoints — Member 1.
- Forecast/anomaly/data-quality calculations or analytical metrics — Member 3.
- `ResultEnvelope` persistence or `AlertCandidate` production — Member 1.
- Changing analytical evidence/confidence during alert or case processing.
- A polished frontend or broad component library.
- Any endpoint that transfers, converts, settles, refills, recovers, reverses, blocks, freezes, accuses, or makes a fraud decision.

## 4. Endpoints you own

### MVP endpoints

| Group | Endpoint | Core responsibility |
|---|---|---|
| Auth | `POST /api/v1/auth/demo-login` | Issue demo JWT/session for a seeded user/role |
| Profile | `GET /api/v1/me` | Return profile, locale, roles and scopes |
| Profile | `PATCH /api/v1/me/preferences` | Update preferred locale only |
| Alerts | `GET /api/v1/alerts` | Authorized filtered alert queue |
| Alerts | `GET /api/v1/alerts/{alertId}` | Structured alert, evidence references and linked case |
| Alerts | `GET /api/v1/alerts/{alertId}/explanations` | Saved localized render snapshots |
| Alerts | `POST /api/v1/alerts/{alertId}/cases` | Idempotently open a routed case when allowed |
| Cases | `GET /api/v1/cases` | Authorized case work queue |
| Cases | `GET /api/v1/cases/{caseId}` | Case, source alert, owner, next step and status |
| Cases | `GET /api/v1/cases/{caseId}/timeline` | Chronological evidence/workflow history |
| Cases | `POST /api/v1/cases/{caseId}/assignments` | Assign/reassign/escalation ownership event |
| Cases | `POST /api/v1/cases/{caseId}/acknowledge` | Legal `open → acknowledged` transition |
| Cases | `POST /api/v1/cases/{caseId}/escalate` | Legal escalation plus target/reason |
| Cases | `POST /api/v1/cases/{caseId}/resolve` | Resolve with mandatory summary |
| Cases | `POST /api/v1/cases/{caseId}/notes` | Append immutable case note |
| Cases | `POST /api/v1/cases/{caseId}/review` | Record benign/follow-up/data-issue/unusual/inconclusive review, never fraud verdict |
| Notification | `GET /api/v1/notifications` | Caller's authorized in-app notifications |
| Notification | `POST /api/v1/notifications/{notificationId}/read` | Idempotently mark caller's notification read |
| Audit | `GET /api/v1/cases/{caseId}/audit-events` | Authorized append-only audit trail |

### Stretch endpoint

- `POST /api/v1/cases/{caseId}/support-requests` only after the Hour 12 MVP gate. It records coordination through an approved external process; it cannot move money.

## 5. Tables and policies you own

From `schema.md`:

- `app_users`, `user_access_scopes`.
- `alerts` and three alert-source link tables.
- `explanation_templates`, `alert_explanations`.
- `routing_rules`.
- `cases`, `case_assignments`, `case_status_history`, `case_notes`.
- `notifications`, `case_reviews`, `audit_events`.
- RLS/grants and workflow/security triggers for these tables.
- Your part of `v_case_timeline` or its service-level equivalent.

Member 1 owns providers, areas, outlets, analytical source records, and their repositories. Reference those records through frozen IDs/contracts; do not duplicate their source of truth.

## 6. Contracts to freeze in Phase 1

### 6.1 `AlertCandidate` consumer

Required candidate fields:

| Field | Validation |
|---|---|
| `candidate_version` | Supported version only |
| `alert_type` | `liquidity`, `anomaly`, `combined`, or `data_quality` |
| `outlet_id` | Must resolve through Member 1 scope contract |
| `provider_id` | Required for provider alert; null only for shared-cash alert |
| `severity` | Allowed severity enum |
| `source_result_ids` | At least one typed persisted projection/flag/quality ID |
| `detected_at` | UTC timestamp |
| `deduplication_key` | Stable per condition/window/scope |
| `structured_variables` | Situation, evidence, uncertainty, safe next-step variables only |
| `plausible_benign_explanation` | Required for anomaly/combined candidate |
| `requires_case` | Boolean |
| `recommended_next_step` | Human/advisory action only |

Validation rules:

- Reject a candidate whose provider/outlet/source IDs disagree.
- Reject unsupported/unsafe wording variables.
- Reject suppressed anomaly output as an anomaly or combined candidate.
- Do not copy raw transaction arrays when typed source links are sufficient.
- Never modify confidence/evidence supplied by the persisted analytical result.

### 6.2 Member 1 reference/scope contract

You need versioned read-only lookups for:

- Provider exists/active.
- Outlet exists/active and area.
- Outlet-provider account belongs to the outlet/provider pair.
- Analytical source result belongs to the claimed outlet/provider and is alertable.
- Current caller scope can be evaluated against provider/outlet/area.

Do not query Member 1 repositories directly from your modules; use the agreed service interface.

### 6.3 API behavior

- Every mutating POST accepts `Idempotency-Key`.
- Case mutations require current `version` or `If-Match`.
- Stale version returns `409 Conflict`.
- Cross-provider unauthorized lookup uses the same `404` shape as a missing record.
- Error shape: `{ error: { code, message, request_id, details } }` with safe details.
- Locale or `Accept-Language` chooses a saved render, falling back to English.
- Workflow mutation and audit event commit in the same database transaction.

## 7. Security and workflow rules

### 7.1 Role/scope matrix

| Role | Minimum scope | Allowed workflow visibility/action |
|---|---|---|
| `agent` | Outlet required | Own outlet combined alert/case view; actions only when assigned/allowed |
| `field_officer` | Provider + area | Assigned provider/area cases |
| `area_manager` | Provider + area | Provider/area queue and authorized escalation actions |
| `provider_ops` | Provider required | Own-provider alerts/cases only |
| `risk_analyst` | Provider required | Escalated own-provider cases/reviews |
| `management` | Aggregate/read-only by default | No raw cross-provider evidence unless explicitly scoped |
| `admin` | Demo/setup only | Never presented as an operational shortcut in demo |

Scope evaluation must be explicit. A missing provider scope is not a wildcard.

### 7.2 Case transition matrix

| From | To | Required data |
|---|---|---|
| none | `open` | Alert, routing rule/target role, recommended next step |
| `open` | `acknowledged` | Authorized actor, expected version |
| `open` | `escalated` | Target role/user, reason, expected version |
| `acknowledged` | `escalated` | Target role/user, reason, expected version |
| `acknowledged` | `resolved` | Resolution summary, expected version |
| `escalated` | `resolved` | Resolution summary, expected version |

Reject all other transitions. Reopening is outside the MVP.

### 7.3 Alert immutability

After publication, type, severity, scope, source links, structured payload, detected time, and rendered explanation snapshots are immutable. Only lifecycle metadata such as `state` or `supersedes_alert_id` may change, and every change is audited.

### 7.4 Audit rules

Audit at minimum:

- Alert publication/state change.
- Case creation and routing decision.
- Assignment/reassignment.
- Acknowledgement and escalation.
- Note creation.
- Notification queue/delivery/read where relevant.
- Review and resolution.
- Authorization-sensitive denial event if safe and useful, without leaking the target record.

Audit rows are append-only; application roles cannot update/delete them.

## 8. Checkpoint-by-checkpoint plan

### Master checkpoint ledger

| Clock | Your cumulative deliverables by this checkpoint | Required from Members 1/3 at this checkpoint | What you must unlock next |
|---|---|---|---|
| 00:45 | Endpoint acceptance, schema/table ownership, transition/RBAC matrix draft, threat list | M1 provider/outlet ID contract; M3 evidence/explanation requirements | Auth/scope and candidate-consumer schemas |
| 01:15 | Route/migration outline, safe API/error/idempotency rules, candidate consumer draft | M3 `ResultEnvelope` evidence fields; M1 scope lookup draft | Final `AlertCandidate` validation |
| 01:30 | Approved candidate consumer, dedup/render/routing variable map | M1 `AlertCandidate` v1; M3 alertability/suppression truth table | Executable route and fixture scaffolds |
| 02:00 | Auth/alert/case route modules, workflow migration files, fixtures and policy tests scaffolded | M1 OpenAPI composition and fixture IDs | Independently runnable Member 2 package |
| 02:15 | `P1-M2` runnable coordination/security skeleton | M1 confirms OpenAPI merge; M3 confirms evidence semantics | Auth/scopes and empty workflow foundation |
| 04:00 | Seeded demo identities/scopes, demo login, `/me`, middleware and denial tests | M1 stable provider/outlet IDs and lookup behavior | Alert/case skeleton persistence and empty queues |
| 05:00 | `P2-M2`, auth/profile routes, scoped empty alert/case queues and thin case shell | M1 candidate fixtures/IDs for Phase 3 | Immutable alert, routing and case creation work |
| 06:30 | Alert/source/template/routing persistence, render tests and candidate fixture consumption | M1 persisted candidate fixture; M3 evidence expectations | Live candidate handoff |
| 06:50 | First live Member 1 candidate accepted/deduplicated/routed | M1 live candidate IDs | Initial case and alert API verification |
| 07:30 | `P3-M2`, alert/explanation routes, initial cases, routing and thin controls | M1 result trace; M3 evidence consistency review | Full lifecycle/security implementation |
| 09:15 | Case actions, notification/timeline/audit, JWT/RBAC/RLS, idempotency/concurrency build | M1 scope lookup; M3 adversarial matrix | Same security matrix run on both API groups |
| 10:00 | `P4-M2`, secured coordination APIs and reproducible defect status | M3 test report; M1 stable IDs/contracts | Live workflow integration |
| 11:00 | Workflow fixtures replaced; login and core case path connected | M1 release candidate/candidate IDs; M3 smoke tests | Full release-candidate Scenario D |
| 12:00 | `P5-M2`, secure workflow demo and resolved Scenario D with audit | M3 RC regression; M1 frozen runtime | Workflow/security reliability measurement |
| 13:00 | Coverage, transition, notification, audit, denial and concurrency raw results | M3 safety/adversarial outcomes | Signed-off workflow evidence |
| 13:30 | `P6-M2`, final reliability/security evidence and responsible-use inputs | M1 RC identifier/latency context; M3 analytical caveats | Documentation package |
| 14:00 | Auth/workflow/security documentation draft and responsibility note | M3 false-positive/human-review language | Final consistent docs |
| 14:30 | `P7-M2`, Scenario D narration, security/responsibility slides | M1 slide/reset format; M3 analytical transition | Rehearsal-ready segment |
| 14:45 | First workflow/security rehearsal and issue list | M1/M3 complete sequence | Timing/wording corrections only |
| 15:10 | Corrected second rehearsal and backup path | M1/M3 final transitions | Freeze presentation and permissions |
| 15:30 | Rehearsed Scenario D, provider denial and audit segment | M1 release ID; M3 final result expectations | Critical access/workflow checks |
| 15:45 | Demo login, denial, lifecycle, notification, audit and permission sign-off | M1 frozen build | Observe final demo; no refactor |
| 16:00 | Final coordination/security sign-off | Submission confirmation from Member 1 | Work complete |

## Phase 1 — API/Schema Contract and Executable Scaffolding

**Time:** 00:00–02:15  
**Phase output:** `P1-M2` runnable coordination/security API skeleton.

### 00:00–00:45 — Scope, workflow and threat freeze

Tasks:

1. Review `schema.md` §§4, 6.5–6.6, 10, 13, 15–17.
2. Confirm all owned endpoints and MVP/stretch boundary.
3. Draft role/scope matrix and legal case transitions.
4. List threats: cross-provider enumeration, IDOR, stale update, duplicate POST, evidence mutation, unsafe render, audit omission, token misuse.
5. Freeze safe error and advisory-language rules.

Deliverables at 00:45:

- Endpoint acceptance checklist.
- Table/migration ownership list.
- Transition and authorization matrix drafts.
- Threat/abuse-case list.
- Questions for Member 1 scope lookup and Member 3 evidence needs.

Prerequisites needed from others:

- Member 1: provider/outlet/account identifier rules and service-boundary draft.
- Member 3: required analytical evidence, confidence, benign context and suppression semantics.

Prerequisites you provide next:

- Exact workflow fields, explanation variables, routing needs, and policy assertions.

### 00:45–01:15 — API policy and candidate consumer draft

Tasks:

1. Define auth/profile request/response fixtures.
2. Define standard safe error, request ID, idempotency, and concurrency behavior.
3. Define candidate validation and typed source-link expectations.
4. Define deduplication key behavior and `requires_case` handling.
5. Define template/render sections: situation, evidence, uncertainty, next step, benign context.

Deliverables at 01:15:

- Auth/scope fixture set.
- Candidate-consumer schema draft.
- API error/idempotency/version policy.
- Explanation-variable and routing-variable list.

Prerequisites needed from others:

- Member 3 `ResultEnvelope` v1 evidence fields.
- Member 1 scope/reference lookup draft.

### 01:15–01:30 — `AlertCandidate` compatibility

Tasks:

1. Review Member 1's candidate v1.
2. Verify Member 3 suppression truth table can be enforced without recalculation.
3. Confirm source IDs, scope, severity, explanation variables and benign context are sufficient.
4. Freeze rejection codes for unsafe/invalid candidates.

Deliverables at 01:30:

- Approved candidate-consumer v1.
- Candidate validation/rejection matrix.
- Deduplication and alertability rules.
- Initial routing decision table.

### 01:30–02:00 — Scaffolding

Tasks:

1. Scaffold auth/profile, alert, case, notification and audit route/service/repository modules.
2. Scaffold separate identity/access and workflow migration files.
3. Create fixture-driven route tests.
4. Create placeholder EN/Bangla/Banglish templates using structured variables.
5. Create state-machine and policy-test skeletons.

Deliverables at 02:00:

- Route/service/repository scaffolds.
- Migration file ownership frozen.
- Candidate/auth/case fixtures.
- Executable contract, transition and policy-test skeletons.

### 02:00–02:15 — Phase gate

Deliverables completed so far:

- Endpoint/table ownership, policies, threat list, candidate consumer, scaffolds, fixtures and test skeletons.

Verify before exit:

- Your package starts/loads independently.
- Member 1 can merge your route contract without editing your module.
- Member 3 confirms analytical evidence is not recalculated or mutated.
- No generic `PATCH status` or financial-action endpoint exists.

Prerequisites you need for Phase 2:

- Member 1: frozen providers/outlets/areas IDs and scope lookup contract.
- Member 3: no runtime dependency; retain evidence fixtures for Phase 3.

Prerequisites you provide for Phase 2:

- `P1-M2`, auth fixtures, role/scope matrix, migration scaffolds and empty alert/case API fixtures.

Fallback if late:

- Keep demo login, `/me`, provider scope, alert/case core, EN + one Bangla/Banglish template, legal transitions and audit. Cut optional review/support-request sophistication first.

## Phase 2 — Foundation APIs

**Time:** 02:15–05:00  
**Phase output:** `P2-M2` auth/workflow foundation.

### 02:15–04:00 — Identity, scope and authorization foundation

Tasks:

1. Apply `app_users` and `user_access_scopes` migrations.
2. Seed demo agent, field officer, provider ops, risk analyst and management identities.
3. Implement demo login, current user and locale preference endpoints.
4. Implement provider/outlet/area scope middleware using Member 1 lookup contract.
5. Add same-shape 404 behavior for missing and unauthorized cross-provider IDs.
6. Add route-level policy tests with Provider A/Provider B users.

Deliverables at Hour 4:

- Demo login returns scoped identity.
- `/me` exposes role/scope/locale accurately.
- Provider A cannot enumerate Provider B resources.
- Auth middleware can protect both Member 1 and Member 2 routes through a versioned contract.

Prerequisites needed from Member 1:

- Stable provider/outlet/area IDs.
- Lookup responses for active/inactive/missing records.
- Agreement on how middleware attaches authorized scope to requests.

Prerequisites needed from Member 3:

- Cross-provider test expectations only; no engine dependency.

### 04:00–05:00 — Empty workflow foundation

Tasks:

1. Apply alert/case skeleton migrations required for empty queues.
2. Implement authorized empty `GET /alerts`, `GET /cases`, and case/alert not-found behavior.
3. Build thin case queue/detail controls against fixtures.
4. Test locale preference and scope-filter combinations.
5. Record known auth/security limitations.

Deliverables at Hour 5:

- `P2-M2` working auth/profile APIs.
- Provider-scoped empty alert/case queues.
- Passing cross-provider enumeration tests.
- Thin fixture-driven case shell.
- Known limitation list.

Prerequisites you need for Phase 3:

- Member 1: candidate fixtures, analytical source IDs and source-validation service.
- Member 3: final evidence/benign/suppression expectations.

Prerequisites you provide for Phase 3:

- Auth middleware, scoped user fixtures, alert/case repositories, candidate consumer and routing fixtures.

Exit criteria:

- No application table stores credentials/password hashes/tokens beyond proper auth integration.
- A provider scope is never interpreted as all providers.
- Unauthorized and missing objects are indistinguishable externally.

## Phase 3 — Intelligence-to-Alert Chain

**Time:** 05:00–07:30  
**Phase output:** `P3-M2` routed alert/case endpoints.

### 05:00–06:30 — Immutable alerts, templates and routing

Tasks:

1. Apply alert/source-link/template/routing/initial-case migrations.
2. Validate and consume candidate fixtures.
3. Implement active-alert deduplication.
4. Persist typed source links rather than copied analytics.
5. Render and persist EN plus demo Bangla/Banglish explanations.
6. Implement routing rule resolution: exact provider+area → provider → area → fallback, then priority.
7. Implement initial case creation with recipient role, owner role and recommended next step.
8. Implement alert list/detail/explanation and case list/detail endpoints.

Deliverables at 06:30:

- Candidate fixtures create immutable source-linked alerts.
- Duplicate candidate does not duplicate active alert/case.
- EN and localized explanation snapshots contain all required sections.
- Important alert routes and opens a scoped case.

Prerequisites needed from Member 1:

- Candidate fixtures with persisted source IDs.
- Source/scope validation service.
- Stable outlet/provider/area IDs.

Prerequisites needed from Member 3:

- Confirmation that evidence, uncertainty, benign context and suppression are represented faithfully.

### 06:30–06:50 — Live candidate handoff

1. Consume Member 1's first live candidate.
2. Compare resulting alert with candidate fixture expectation.
3. Confirm analytical evidence/confidence is unchanged.
4. Return structured rejection if source/scope mismatch occurs.

Deliverables at 06:50:

- Live candidate accepted or reproducible contract defect reported.
- Stable alert/case IDs handed back for end-to-end tracing.

### 06:50–07:30 — Route/UI verification

1. Exercise alert list/detail/explanation and case list/detail with demo roles.
2. Confirm unauthorized providers cannot see the live alert/case.
3. Confirm the minimal controls can navigate alert → evidence summary → case.

Deliverables at Hour 7:30:

- `P3-M2` alert/routing/initial-case package.
- One routed Scenario A/B case with localized explanation.
- Deduplication proof.
- Result → candidate → alert → case trace.

Prerequisites you need for Phase 4:

- Member 1: stable scope lookup and candidate IDs under degraded conditions.
- Member 3: adversarial matrix, Scenario C expected advisory/suppression behavior and provider-leakage expectations.

Prerequisites you provide for Phase 4:

- Live case IDs, route fixtures, transition/version contract, role tokens and current security test status.

Exit criteria:

- Suppressed anomaly output cannot become an anomaly/combined alert.
- Published alert evidence is immutable.
- Every high-impact alert render contains situation, evidence, uncertainty and safe next step.
- No text declares fraud or recommends blocking/freezing/transferring value.

## Phase 4 — Safe Coordinated Response

**Time:** 07:30–10:00  
**Phase output:** `P4-M2` secure coordination APIs.

### 07:30–09:15 — Complete lifecycle and security

Tasks:

1. Implement assignment/reassignment with recipient/owner history.
2. Implement acknowledge, escalate and resolve action endpoints with legal transition checks.
3. Implement immutable notes and case review.
4. Implement in-app notifications and read state.
5. Implement case timeline and audit event reads.
6. Write audit rows in the same transaction as mutations.
7. Enforce idempotency for POST actions.
8. Enforce case `version`/`If-Match` and stale-update conflict.
9. Apply grants/RLS and application-layer provider/outlet/area checks.
10. Complete minimal workflow controls.

Deliverables at 09:15:

- Full Scenario D endpoint sequence works on your local build.
- Duplicate mutation does not duplicate state/audit/notification.
- Stale version returns 409 without mutation.
- Provider A denial and no-enumeration behavior pass.
- Audit/timeline show the entire workflow.

Prerequisites needed from Member 1:

- Stable scope lookup and endpoint authorization hook.
- Alert/candidate IDs and outlet/provider/area fixtures.

Prerequisites needed from Member 3:

- Cross-provider, invalid-transition, duplicate-request, concurrency and safe-language expectations.

### 09:15–10:00 — Shared adversarial gate

Rules:

- Member 3 runs the same matrix against both endpoint groups.
- Fix only Member 2 defects.
- Require request/input, expected/actual, release ID and retest before closing a defect.

Deliverables at Hour 10:

- `P4-M2` secured coordination package.
- Passing transition, idempotency, concurrency, notification, audit and provider-boundary tests.
- Scenario D executable without database edits.
- Prioritized remaining defect list.

Prerequisites you need for Phase 5:

- Member 1: release-candidate composition plan, base URL, reset/seed command and live candidate IDs.
- Member 3: A–D regression suite and blocker classifications.

Prerequisites you provide for Phase 5:

- Complete auth/workflow routes, demo identities, role tokens, known-case IDs and Scenario D request sequence.

## Phase 5 — Integration and MVP Freeze

**Time:** 10:00–12:00  
**Phase output:** `P5-M2` secure workflow demo.

### 10:00–11:00 — Replace fixtures and integrate

1. Connect alert/case controls to live routes.
2. Connect Member 1 live candidates to alert/case creation.
3. Verify clean-session demo login and scope propagation.
4. Verify localized explanation selection/fallback.
5. Verify dashboard alert navigation reaches the correct case.
6. Fix only coordination/security defects.

Deliverables at 11:00:

- Live alert/case/notification/audit workflow.
- Known demo users and reset-state case expectations.
- Integration defect list.

### 11:00–12:00 — Release-candidate gate

Run Scenario D against Member 1's release candidate:

1. Login as authorized recipient.
2. Open alert and explanation.
3. Open/verify routed case.
4. Assign/acknowledge.
5. Escalate and add note.
6. Resolve with summary and optionally review.
7. Verify notification and complete audit/timeline.
8. Login as other-provider user and verify denial.
9. Repeat mutations and stale version to verify safety.

Deliverables at Hour 12:

- `P5-M2` secure workflow demo.
- Release-candidate Scenario D evidence.
- Provider-boundary denial evidence.
- Alert immutability and audit-completeness proof.
- Frozen demo identity/permission sheet.

Prerequisites you need for Phase 6:

- Member 1: frozen release ID and data/candidate reset behavior.
- Member 3: final regression/adversarial results and analytical responsibility caveats.

Prerequisites you provide for Phase 6:

- Workflow test outputs, explanation coverage inputs, transition/audit counts, notification results and security-denial evidence.

## Phase 6 — Validation and Observability

**Time:** 12:00–13:30  
**Phase output:** `P6-M2` workflow/security reliability evidence.

### 12:00–13:00 — Measure workflow reliability

Measure at minimum:

- Alert explanation coverage: percentage with situation, evidence, uncertainty and safe next step.
- Legal transition pass rate and invalid transition rejection rate.
- Audit completeness: expected workflow actions with matching audit event.
- Notification delivery/read correctness for defined cases.
- Cross-provider denial success for the security matrix.
- Idempotency and stale-concurrency handling success.

For every result include sample size, method, exact release ID, result and limitation.

Tasks:

1. Run the frozen workflow/security suite.
2. Save raw response/audit summaries without confidential cross-provider content.
3. Verify safe-language and localized-render coverage.
4. Recheck RLS/grants and application authorization both deny forbidden access.

Deliverables at 13:00:

- Raw workflow/security test evidence.
- Numeric coverage/reliability results.
- Provider-boundary proof.
- Known limitation list.

### 13:00–13:30 — Sign-off and responsibility inputs

1. Reconcile evidence with the demo release.
2. Receive Member 3 false-positive/human-review caveats.
3. Draft responsible-use statements for privacy, advisory boundaries and intentionally absent actions.

Deliverables at Hour 13:30:

- `P6-M2` signed-off workflow/security evidence.
- Explanation coverage method/result.
- Audit/transition/notification evidence.
- RBAC/RLS limitation statement.
- Responsible-design source notes.

Prerequisites you need for Phase 7:

- Member 1: final architecture/doc locations and release identifier.
- Member 3: final analytical caveats, false-positive risk and human-review language.

Prerequisites you provide for Phase 7:

- Auth/RBAC/RLS description, alert-vs-case explanation, routing/lifecycle behavior, evidence results, guardrails and limitations.

## Phase 7 — Documentation

**Time:** 13:30–14:30  
**Phase output:** `P7-M2` workflow/security/responsible-design documentation.

Write concise factual sections covering:

1. Demo roles and provider/outlet/area scope rules.
2. Why alerts are immutable and cases are mutable workflows.
3. `AlertCandidate` validation and source-link preservation.
4. Explanation templates and EN/Bangla/Banglish consistency.
5. Routing rule and recipient/owner behavior.
6. Legal case lifecycle, notes, review, notification and audit.
7. Idempotency and optimistic concurrency.
8. Application authorization plus RLS defense in depth.
9. Privacy, human review, false positives and advisory-only boundaries.
10. Explicitly absent actions: transfers, conversion, settlement, refill, recovery, reversal, block, freeze, accusation and fraud verdict.
11. Workflow/security metrics and limitations.

Checkpoint at Hour 14:00:

- Send Member 1 final auth/setup/role instructions and document links.
- Reconcile responsible-design wording with Member 3 analytical caveats.

Deliverables at Hour 14:30:

- `P7-M2` documentation package.
- Scenario D narration and slide content.
- Documentation matches actual endpoints and release behavior.
- No production/regulatory/security-completeness claim.

Prerequisites you need for Phase 8:

- Member 1: final slide format, reset sequence and architecture transition.
- Member 3: transition from Scenario B/metrics into responsibility and coordination.

Prerequisites you provide for Phase 8:

- Scenario D script, demo identities, expected statuses, denial demonstration, responsibility summary and backup captures.

## Phase 8 — Presentation and Rehearsal

**Time:** 14:30–15:30  
**Phase output:** Rehearsed Scenario D/security segment.

### 14:30–14:45 — Prepare

- Confirm demo role/token/session procedure.
- Confirm exact case state and reset behavior.
- Prepare concise explanation of alert versus case.
- Prepare RBAC/provider-boundary denial demonstration.
- Prepare answers on ownership, escalation, human review, audit, idempotency and prohibited actions.

### 14:45 rehearsal 1

Deliverables/checkpoint:

- Scenario D completes inside allocated time.
- Alert → case → assignment → acknowledgement → escalation/note → resolution → audit is visible.
- Provider A denial of Provider B case is visible without leaking details.
- Record only blocking demo/permission/wording issues.

### 15:10 rehearsal 2

Deliverables/checkpoint:

- Final spoken wording and transitions.
- Backup screenshots/responses for login, case flow, audit and denial.
- Final presentation permissions verified.

Deliverables at Hour 15:30:

- Rehearsed Scenario D, provider-boundary and responsibility segment.
- Verified backup workflow/security evidence.
- No mismatch between docs, slides and API behavior.

Prerequisites you need for Phase 9:

- Member 1: frozen release ID/reset output and submission permission state.
- Member 3: final analytical result expectations and safety scan status.

Prerequisites you provide for Phase 9:

- Final demo users/scopes, expected case/audit sequence, denial check and presentation permission checklist.

## Phase 9 — Final Buffer and Submission

**Time:** 15:30–16:00  
**Phase output:** Final coordination/security sign-off.

### 15:30–15:45 — Critical checks

- Demo login and `/me` scopes.
- Alert/detail/explanation access.
- Full case lifecycle and audit/timeline.
- Notification delivery/read.
- Provider A denial of Provider B alert/case/note/audit.
- Duplicate POST idempotency and stale-version conflict.
- Safe wording and localized render.
- Repository/presentation permissions from non-owner view.

Deliverables at 15:45:

- Final Member 2 sign-off or exact blocker statement.
- Passing critical workflow/security test summary.
- Clean provider-boundary result.
- Confirmed presentation/repository permissions.

### 15:45–16:00 — Submission support

- Observe Member 1's final demo using the frozen build.
- Answer workflow/security questions only.
- Fix only a critical Member 2 auth/workflow/security defect and require affected regression retest.
- Do not refactor policies, rename roles, change routing rules or add endpoints.

Final deliverables:

- `P1-M2` through `P7-M2` artifacts present.
- Tested roles/scopes, case transition and routing configuration recorded.
- Final responsible-design and limitation statements present.
- Submission workflow/security behavior matches the frozen release.

## 9. Test matrix

| Area | Minimum tests |
|---|---|
| Auth/profile | Valid/invalid demo login, inactive user, `/me`, locale preference, expired/invalid token |
| Scope | Own outlet, assigned area/provider, other provider, other outlet, missing record, inactive provider/outlet, management aggregate restriction |
| Candidate | Valid types, scope mismatch, missing source, unsupported version, suppressed anomaly, missing benign context, unsafe next step |
| Deduplication | Same key repeated, superseding condition, concurrent duplicate candidates |
| Explanation | EN required, Bangla/Banglish demo, fallback, all sections, immutable snapshots, prohibited language |
| Routing | Exact provider+area, provider fallback, area fallback, global fallback, priority tie behavior |
| Case creation | `requires_case`, no-case advisory, duplicate open request, missing routing/owner/next step |
| Transition | Every legal transition, every illegal transition, required reason/summary, unauthorized actor |
| Concurrency | Correct version, stale version, simultaneous updates, no partial audit/state |
| Assignment/notes/review | Valid scope, immutable history, safe note content, non-fraud review outcomes |
| Notification | Queue, deliver, read, duplicate read, wrong recipient, safe payload scope |
| Audit | One matching event per mutation, ordering, actor/request ID, append-only permission |
| RLS/RBAC | Provider A/B isolation for alert/case/note/evidence/notification/audit; outlet/area boundaries |
| Errors | Same 404 shape for missing/forbidden; no confidential details; request ID present |
| E2E | Scenario D complete, provider denial, audit trail, reset/replay behavior |

## 10. Workflow invariant checklist

- Published alert analytical content cannot be edited.
- Every alert has at least one typed analytical/quality source.
- Suppressed anomaly cannot create anomaly/combined alert.
- Every high-impact alert has complete English explanation.
- Demo alert has Bangla or Banglish explanation.
- Case cannot exist without alert, scope, recipient/owner role and safe next step.
- Case current state matches latest legal status history.
- Case current owner matches latest valid assignment.
- Resolve requires summary and timestamp.
- Mutation and audit commit atomically.
- Idempotent repeat returns original result.
- Stale update returns 409 and changes nothing.
- Cross-provider lookup leaks no record existence.
- Notes/reviews contain no credentials, real identities or definitive fraud verdict.

## 11. Defect reporting template

```text
Title:
Owner: Member 1 / Member 2 / Member 3
Release/commit:
Role + provider/outlet/area scope:
Endpoint + request:
Expected status/body/state/audit:
Actual status/body/state/audit:
Failed invariant:
Severity: blocker / high / normal
Reproduction steps:
Evidence file:
Retest required:
```

Never include secrets/tokens or another provider's confidential payload in a shared defect report.

## 12. Cut order if behind

Cut in this order:

1. Stretch support-request endpoint.
2. Case review UI; retain review API only if already stable.
3. Additional routing variants; retain provider+area and fallback.
4. Multiple localized alert types; retain English for all and one Bangla/Banglish demo alert.
5. Visual timeline polish; retain timeline/audit data.

Never cut:

- Provider-boundary authorization.
- Immutable alerts and evidence links.
- Receiver, owner, next step and legal lifecycle.
- Assignment, acknowledgement, escalation and resolution.
- Complete audit trail.
- Idempotency/concurrency safety for demo mutations.
- Safe advisory language and human-review boundary.

## 13. Personal completion checklist

- [ ] All 19 MVP Member 2 endpoints implemented and scoped.
- [ ] Demo login and `/me` roles/scopes accurate.
- [ ] Provider A cannot enumerate/read/mutate Provider B records.
- [ ] `AlertCandidate` consumer validates scope/source/suppression.
- [ ] Active-alert deduplication works.
- [ ] Published analytical alert content is immutable.
- [ ] English explanations complete; demo localized explanation works.
- [ ] Routing produces recipient/owner and safe next step.
- [ ] Case lifecycle accepts only legal transitions.
- [ ] Assignments, notes, review, notifications and timeline work.
- [ ] Audit is complete and append-only.
- [ ] Idempotency and stale-version conflict tested.
- [ ] Scenario D completes without database edits.
- [ ] Workflow/security evidence includes methods, samples and limitations.
- [ ] Responsible-design documentation complete.
- [ ] Scenario D/security presentation rehearsed.
- [ ] Final roles/routing/release versions recorded.
