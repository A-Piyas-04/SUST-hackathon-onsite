# Authorization Fix Checklist

**Status:** Open — tracking gaps between intended policy and current implementation  
**Authority:** `docs/schema.md` §15 (RLS & authorization matrix), `docs/frontend/frontend-page-plan.md` §F (role-based navigation)  
**Principle:** Backend policy is authoritative. Frontend gating improves UX; API enforcement is required for security.

---

## 1. Problem summary

Today, every authenticated demo user can see and use nearly every feature in the GUI. Root causes are split:

| Layer | Design | Implementation gap |
| --- | --- | --- |
| **Frontend** | Role-based landing, tabs, and actions defined in `frontend-page-plan.md` | Single `page.tsx` shell shows all 7 tabs, outlet picker, and all case actions to every role |
| **Backend** | `authz.py` + schema §15 define provider/outlet scope and role matrix | Scope enforced only on alerts/cases/notifications; ledger/analytics/simulation routes are auth-only |

The application connects with a **privileged database role** (`authz.py` header). PostgreSQL RLS is defense-in-depth only. **Application-layer checks must gate every outlet/provider-confidential route.**

---

## 2. Policy reference (intended behavior)

### 2.1 Scope rules (who can see which outlet/provider data)

| Role | Scope source | Outlet access | Provider-confidential access |
| --- | --- | --- | --- |
| `agent` | Required `outlet_id` | Own outlet combined view only | Own outlet, all providers on dashboard; no other outlet |
| `field_officer` | `provider_id` + `area_id` | Outlets in assigned area | Assigned provider only |
| `area_manager` | `provider_id` + `area_id` | Outlets in assigned area | Assigned provider only |
| `provider_ops` | `provider_id` | Outlets with provider account | Own provider only |
| `risk_analyst` | `provider_id` (+ optional area) | Case-linked / provider-scoped | Own provider only |
| `management` | Optional provider/area; default aggregate | Aggregate-safe summaries | No raw cross-provider evidence by default |
| `admin` | Demo/setup | Configured demo scope | Full demo scope for seed/reset |

Helpers to mirror: `has_outlet_scope()`, `has_provider_scope()`, `can_access_scope()` in `backend/app/core/authz.py` and migration `006` (`app.has_outlet_scope`, `app.has_provider_scope`).

### 2.2 Action rules (who can mutate what)

Derived from `schema.md` §15 rows 908–909 and §15.1 stakeholder restrictions.

| Action | Agent | Field/Area ops | Provider ops | Risk analyst | Management | Admin |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Read own/scoped outlet dashboard | ✓ | ✓ scoped | ✓ provider slice | ✓ provider slice | ✓ aggregate | ✓ |
| Read raw provider transactions | ✓ own outlet | ✓ scoped | ✓ own provider | ✓ case-linked | ✗ aggregate only | ✓ |
| Open case from alert | Limited / assigned | ✓ scoped | ✓ own provider | ✓ escalated | ✗ | ✓ |
| Acknowledge case | If owner/assigned | ✓ if owner | ✓ if owner | ✗ | ✗ | ✓ |
| Escalate case | ✗ or limited | ✓ | ✓ | ✗ | ✗ | ✓ |
| Assign case owner | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ |
| Add case note | ✓ if participant | ✓ | ✓ | ✓ | ✗ | ✓ |
| Add risk review | ✗ | ✗ | ✗ | ✓ escalated | ✗ | ✓ |
| Resolve case | ✗ or limited | ✓ if owner | ✓ if owner | ✗ | ✗ | ✓ |
| Simulation run / fault / reset | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Internal analytics publish / run | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Ingestion batch POST | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 3. Backend fix checklist

### 3.1 Infrastructure (do first)

- [ ] **B0.1** Add `require_outlet_access(session, user, outlet_id)` dependency/helper that calls `has_outlet_scope()` and raises `SafeNotFoundError` on deny (match coordination layer pattern).
- [ ] **B0.2** Add `require_provider_access(session, user, provider_id, outlet_id)` for provider-confidential reads.
- [ ] **B0.3** Add `require_role_action(user, action: CaseAction | ...)` for mutation authorization (separate from scope).
- [ ] **B0.4** Add `require_admin(user)` for simulation, ingestion, and internal orchestration routes.
- [ ] **B0.5** Filter `GET /outlets` server-side to authorized outlets only (never return full catalog to agent).
- [ ] **B0.6** Document 404 vs 403 policy: confidential resources use safe 404 (`SafeNotFoundError`); explicit forbidden actions may use 403 with `forbidden` code.

**Files:** `backend/app/core/authz.py`, new `backend/app/core/deps.py` (optional FastAPI dependencies).

---

### 3.2 Reference & ledger routes (`backend/app/api/v1/reference.py`)

Current: `require_authenticated` only. Services do not receive `UserContext`.

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B1.1 | GET | `/api/v1/providers` | Filter to providers visible in user's scope (agent: all at outlet; ops: assigned provider) | Agent sees bkash/nagad/rocket at own outlet; nagad ops does not see bkash-only leakage |
| B1.2 | GET | `/api/v1/areas` | Filter to authorized areas | Area manager sees Market; unrelated area hidden |
| B1.3 | GET | `/api/v1/outlets` | Return only scoped outlets | Agent gets 1 outlet; management gets aggregate list per policy |
| B1.4 | GET | `/api/v1/outlets/{outlet_id}` | `require_outlet_access` | Cross-outlet agent → 404 |
| B1.5 | GET | `/api/v1/outlets/{outlet_id}/dashboard` | `require_outlet_access` | Agent on outlet2 cannot read outlet1 dashboard |
| B1.6 | GET | `/api/v1/outlets/{outlet_id}/transactions` | `require_provider_access` when `provider_code` set; else outlet scope with provider filtering per row | Cross-provider ops denied |
| B1.7 | GET | `/api/v1/outlets/{outlet_id}/balances/history` | Same as B1.6 by `reserve_type` / `provider_code` | Shared cash: outlet scope; provider balance: provider scope |
| B1.8 | GET | `/api/v1/outlets/{outlet_id}/data-quality` | Outlet scope; filter assessments to authorized providers | Management aggregate-only variant if applicable |
| B1.9 | GET | `/api/v1/outlets/{outlet_id}/data-quality/history` | Same as B1.8 | Cross-outlet denied |

**Files:** `reference.py`, `backend/app/services/ledger/reader.py`, `backend/app/services/quality/foundation.py`.

---

### 3.3 Analytics routes (`backend/app/api/v1/analytics.py`)

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B2.1 | GET | `/api/v1/outlets/{outlet_id}/liquidity-projections` | `require_outlet_access`; filter provider rows by scope | Cross-outlet denied |
| B2.2 | GET | `/api/v1/outlets/{outlet_id}/anomaly-flags` | `require_outlet_access`; provider filter | Cross-provider denied |
| B2.3 | GET | `/api/v1/anomaly-flags/{flag_id}` | Load flag → `can_access_scope(outlet_id, provider_id)` | Nagad ops cannot read bKash flag |
| B2.4 | POST | `/api/v1/internal/analytics/liquidity/run` | `require_admin` + outlet scope on request body | Agent → 403 |
| B2.5 | POST | `/api/v1/internal/analytics/anomalies/run` | `require_admin` + outlet scope | Agent → 403 |

**Files:** `analytics.py`, `backend/app/services/analytics/reader.py`.

---

### 3.4 Simulation routes (`backend/app/api/v1/simulation.py`)

Per schema §15: *Routing/config/seed — admin/service only.*

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B3.1 | GET | `/api/v1/simulations/scenarios` | `require_admin` (or read-only catalog for demo presenters if product decides otherwise) | Agent → 403 |
| B3.2 | POST | `/api/v1/simulations/runs` | `require_admin` + `require_outlet_access` on `outlet_id` in body | Agent → 403 |
| B3.3 | GET | `/api/v1/simulations/runs/{run_id}` | `require_admin` or scoped read tied to run's outlet | Non-admin denied or scoped |
| B3.4 | POST | `/api/v1/simulations/runs/{run_id}/reset` | `require_admin` | Agent → 403 |
| B3.5 | POST | `/api/v1/simulations/runs/{run_id}/faults` | `require_admin` | Agent → 403 |
| B3.6 | PATCH | `/api/v1/simulations/runs/{run_id}/faults/{fault_id}` | `require_admin` | Agent → 403 |

**Files:** `simulation.py`, `backend/app/services/simulation/run_service.py`, `fault_service.py`.

---

### 3.5 Ingestion routes (`backend/app/api/v1/ingestion.py`)

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B4.1 | POST | `/api/v1/ingestion/batches` | `require_admin` only — never callable from browser personas | Any non-admin → 403 |

---

### 3.6 Alert routes (`backend/app/api/v1/alerts.py`)

Scope checks exist in service layer. Remaining gaps:

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B5.1 | GET | `/api/v1/alerts` | ✓ scope filter in service — verify outlet_id query respects scope | Agent listing excludes other outlets |
| B5.2 | GET | `/api/v1/alerts/{alert_id}` | ✓ `require_alert` — keep | Already covered in `test_authorization.py` |
| B5.3 | GET | `/api/v1/alerts/{alert_id}/explanations` | ✓ via `require_alert` — keep | Cross-provider → 404 |
| B5.4 | POST | `/api/v1/internal/alerts/publish` | `require_admin` + outlet scope | Agent → 403 |

---

### 3.7 Case routes (`backend/app/api/v1/cases.py`)

Scope checks exist; **role-action matrix missing** on mutations.

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B6.1 | GET | `/api/v1/cases` | ✓ scope filter — verify | Agent sees own-outlet cases only |
| B6.2 | GET | `/api/v1/cases/{case_id}` | ✓ `require_case` — keep | Cross-provider → 404 |
| B6.3 | GET | `/api/v1/cases/{case_id}/timeline` | ✓ scope — keep | |
| B6.4 | GET | `/api/v1/cases/{case_id}/audit-events` | Consider stricter than case read (schema §15) | |
| B6.5 | POST | `/api/v1/alerts/{alert_id}/cases` | Scope + role: ops roles; agent only if assigned policy | Agent open case policy test |
| B6.6 | POST | `/api/v1/cases/{case_id}/assignments` | `require_role_action(assign)` — ops only | Agent → 403 |
| B6.7 | POST | `/api/v1/cases/{case_id}/acknowledge` | Owner or authorized ops role; deny management | Management → 403 |
| B6.8 | POST | `/api/v1/cases/{case_id}/escalate` | Ops roles only; deny agent/management | Agent → 403 |
| B6.9 | POST | `/api/v1/cases/{case_id}/resolve` | Ops owner roles; deny management/risk | Management → 403 |
| B6.10 | POST | `/api/v1/cases/{case_id}/notes` | Scoped participants; deny management | |
| B6.11 | POST | `/api/v1/cases/{case_id}/review` | `risk_analyst` only (escalated case) | Provider ops → 403 |

**Files:** `backend/app/services/coordination/cases.py`.

---

### 3.8 Notification routes (`backend/app/api/v1/notifications.py`)

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B7.1 | GET | `/api/v1/notifications` | ✓ recipient filter in service — verify role+scope match | User A does not see User B notifications |
| B7.2 | POST | `/api/v1/notifications/{id}/read` | ✓ recipient check — keep | |

---

### 3.9 Auth routes (`backend/app/api/v1/auth.py`)

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B8.1 | POST | `/api/v1/auth/demo-login` | Ensure server assigns scope; client cannot pick arbitrary `outlet_id` | |
| B8.2 | GET | `/api/v1/me` | Return `roles`, `scopes`, and optional `permissions[]` for frontend gating | Frontend can derive tab visibility |
| B8.3 | PATCH | `/api/v1/me/preferences` | ✓ self only — keep | |

---

### 3.10 Stub / validation routes (`backend/app/api/v1/stubs.py`)

| ID | Method | Route | Required fix | Test to add |
| --- | --- | --- | --- | --- |
| B9.1 | GET | `/api/v1/validation/results` | When implemented: `admin` or `management` read grant only | Agent → 403 |

---

## 4. Frontend fix checklist

Current shell: `frontend/src/app/page.tsx` — all tabs and outlet picker for every user.  
Target: `docs/frontend/frontend-page-plan.md` §E–F.

### 4.1 Session & navigation infrastructure

- [ ] **F0.1** Add `lib/authz.ts` with pure functions: `canSeeTab(role, tab)`, `canPerformCaseAction(role, action)`, `defaultLandingRoute(principal)`, `authorizedOutlets(principal, outlets)`.
- [ ] **F0.2** Bootstrap from `GET /api/v1/me` — use server `scopes` as source of truth (not client-side role guessing).
- [ ] **F0.3** Post-login redirect by role: agent → own outlet dashboard; ops/risk → work queue (or cases tab interim); admin → scenarios; management → aggregate queue.
- [ ] **F0.4** Add `/forbidden` route (or inline forbidden state) when user deep-links to unauthorized `outletId`.
- [ ] **F0.5** Hide nav items the role cannot use (do not rely on API errors alone).

---

### 4.2 Tab visibility matrix (maps to current monolith tabs)

| Tab (current) | Agent | Field/Area ops | Provider ops | Risk analyst | Management | Admin |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Dashboard | ✓ own outlet | ✓ scoped | ✓ scoped | ✓ scoped read-only | ✓ aggregate | ✓ |
| Liquidity | ✓ own | ✓ scoped | ✓ scoped | ✓ scoped | Summary only | ✓ |
| Anomalies | ✓ own limited | ✓ scoped | ✓ scoped | ✓ full provider | Hidden raw | ✓ |
| Scenarios & Faults | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Alerts | ✓ scoped | ✓ scoped | ✓ scoped | ✓ scoped | Sanitized read | ✓ |
| Cases | ✓ assigned/limited | ✓ scoped | ✓ scoped | ✓ review | Read-only | ✓ |
| Notifications | ✓ personal | ✓ personal | ✓ personal | ✓ personal | ✓ summary | ✓ |

**Files:** `frontend/src/app/page.tsx` — filter `TABS` before render.

---

### 4.3 Component-level gating

| ID | Component | Fix |
| --- | --- | --- |
| F1.1 | `page.tsx` outlet `<select>` | Hide for `agent`; lock `outletId` to `scopes[0].outlet_id`. Show filtered list for ops/management. |
| F1.2 | `ScenarioPanel.tsx` | Render only when `admin` role (or dedicated demo route). Remove from default agent ops flow. |
| F1.3 | `CasePanel.tsx` `CaseActions` | Show Acknowledge/Escalate/Resolve/Review buttons per role matrix; management = read-only. |
| F1.4 | `AlertsPanel.tsx` | Hide "open case" for roles without create permission. |
| F1.5 | `AnomalyPanel.tsx` | Management: summary cards only; hide raw transaction drill-down if policy requires. |
| F1.6 | `LiquidityPanel.tsx` | Management: summary-only view. |
| F1.7 | `LoginPanel.tsx` | Keep role switcher for demo, but label as "demo identity" not permission grant. |

---

### 4.4 API client hygiene

Per `frontend-page-plan.md` §G.2 — normal frontend code must **not** call:

- [ ] **F2.1** Remove or guard `runLiquidityAnalytics` / `runAnomalyAnalytics` in `ScenarioPanel` for non-admin (prefer server-side pipeline on simulation run).
- [ ] **F2.2** Remove or guard `publishAlerts` for non-admin.
- [ ] **F2.3** Handle 403/404 uniformly in `lib/api.ts` — show scope-safe message ("Not available or outside your access scope").

**Files:** `frontend/src/lib/api.ts`, panel components.

---

## 5. Test checklist

### 5.1 Backend tests to add (`backend/tests/`)

| ID | Test file (suggested) | Scenario |
| --- | --- | --- |
| T1 | `tests/phase5/test_authorization.py` | Agent cannot `GET` dashboard for outlet2 → 404 |
| T2 | `tests/phase5/test_authorization.py` | Management cannot `POST` resolve case → 403 |
| T3 | `tests/phase5/test_authorization.py` | Agent cannot `POST` simulation run → 403 |
| T4 | `tests/phase5/test_authorization.py` | Risk analyst can review escalated case; cannot resolve |
| T5 | `tests/phase5/test_authorization.py` | `GET /outlets` returns only authorized outlets per role |
| T6 | `tests/phase5/test_authorization.py` | Nagad ops cannot `GET` anomaly flag for bKash-only flag → 404 |
| T7 | `tests/phase5/test_authorization.py` | Non-admin cannot `POST /internal/alerts/publish` → 403 |
| T8 | `tests/test_rls.py` | Keep existing RLS tests — app-layer must match RLS intent |

### 5.2 Frontend tests (when test harness exists)

| ID | Scenario |
| --- | --- |
| T9 | Agent login: Scenarios tab not in DOM |
| T10 | Agent login: no outlet picker; dashboard uses scoped outlet |
| T11 | Management login: case action buttons hidden |
| T12 | Admin login: all tabs visible |

### 5.3 Manual demo verification

| Persona | Must work | Must be denied |
| --- | --- | --- |
| Agent (Outlet 001) | Own dashboard, alerts at outlet1, assigned cases | Outlet2 data, scenarios, case escalate/resolve |
| bKash ops | bKash alerts/cases in scope | Nagad confidential alert detail |
| Management | Aggregate queue, read-only cases | Raw anomaly transactions, case mutations, scenarios |
| Admin | Simulation, faults, publish pipeline | N/A (full demo scope) |

---

## 6. Recommended implementation order

1. **Backend B0** — shared helpers (`require_outlet_access`, `require_admin`, `require_role_action`).
2. **Backend B1–B3** — ledger, analytics, simulation (highest data-exposure risk).
3. **Backend B6** — case mutation role matrix.
4. **Backend B5.4, B2.4–B2.5, B4.1** — lock internal/admin orchestration.
5. **Frontend F0 + F1** — tab, outlet, and action gating wired to `/me`.
6. **Tests T1–T8** — lock behavior before demo hardening.
7. **Frontend F2** — remove browser calls to internal routes for non-admin.

---

## 7. Acceptance criteria (done when)

- [ ] No authenticated non-admin user can read another outlet's dashboard, transactions, or analytics via API (404, no existence leak).
- [ ] Cross-provider confidential reads remain denied (existing alert tests still pass).
- [ ] Case mutations return 403 for roles outside the action matrix (management cannot resolve).
- [ ] Simulation, fault, reset, publish, and ingestion routes reject non-admin with 403.
- [ ] `GET /outlets` returns only authorized outlets per principal.
- [ ] Frontend hides tabs and actions inconsistent with role; agent has no outlet picker.
- [ ] `GET /api/v1/me` exposes enough scope/permission data for the UI to gate without duplicating policy logic in full.
- [ ] New authorization tests added and passing in CI.
- [ ] `docs/openapi/openapi.v1.json` updated if error responses or `/me` shape changes.

---

## 8. Related documents

| Document | Relevance |
| --- | --- |
| `docs/schema.md` §15 | Authoritative authorization matrix |
| `docs/frontend/frontend-page-plan.md` §E–G | Target navigation and API mapping |
| `docs/adr/0004-rls-claims-shim-and-guarded-roles.md` | RLS vs app-layer responsibility |
| `backend/app/core/authz.py` | Scope helper implementation |
| `backend/tests/phase5/test_authorization.py` | Existing cross-provider tests |
| `backend/tests/test_rls.py` | Database-level isolation tests |

---

## 9. Out of scope for this checklist

- Replacing demo bearer tokens with production Supabase JWT (Phase 2 auth shim).
- Full multi-page Next.js route split (`/work`, `/cases/[id]`, etc.) — tracked in frontend page plan; this checklist covers minimum viable gating on the current monolith.
- Management aggregate view implementation details (sanitization rules) — separate UX task once read paths are scoped.
