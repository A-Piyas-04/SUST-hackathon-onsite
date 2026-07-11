# Frontend Redesign Plan
## Multi-Provider Agent Liquidity & Coordination Platform
**Hackathon: bKash presents SUST CSE Carnival 2026**

---

## 0. Overview & Design Philosophy

This document is the complete implementation blueprint for the frontend — from visual design tokens to page-by-page UX specifications, role-based access rules, component architecture, and API wiring. Every decision maps to a backend feature that already exists.

**Core UI principles:**
1. **Clarity over decoration.** Every pixel earns its place by surfacing information the user needs to act.
2. **Role context is always visible.** Who you are and what you can see is never ambiguous.
3. **Confidence and uncertainty are first-class.** Degraded data must *look* degraded; high-confidence output must look trustworthy.
4. **Advisory language only.** No UI element implies a financial action, fraud verdict, or account block.
5. **Evidence before action.** Every alert, case, and anomaly shows its reasoning inline — no black-box scores.

---

## 1. Design System

### 1.1 Color Palette

The palette draws from the visual vernacular of mobile money infrastructure: the deep trust blues of Bangladeshi banking, the amber of cash-warning, and the clean separation between providers using their own brand identity.

```
--color-bg-base:       #0D1117   /* near-black canvas — financial terminal feel */
--color-bg-surface:    #161B22   /* card/panel surface */
--color-bg-elevated:   #21262D   /* modals, dropdowns, tooltips */
--color-bg-subtle:     #30363D   /* table rows, section dividers */

--color-border:        #30363D
--color-border-muted:  #21262D

--color-text-primary:  #E6EDF3   /* headings, primary content */
--color-text-secondary:#8B949E   /* labels, metadata, timestamps */
--color-text-muted:    #484F58   /* placeholders, disabled */

/* Semantic */
--color-success:       #3FB950   /* fresh data, resolved cases */
--color-warning:       #D29922   /* stale data, medium confidence */
--color-danger:        #F85149   /* missing data, high severity, shortages */
--color-info:          #388BFD   /* informational alerts, projected states */
--color-accent:        #58A6FF   /* interactive elements, links, focus rings */

/* Provider identity colors — used as accent only, never full backgrounds */
--color-bkash:         #E2136E   /* bKash magenta */
--color-nagad:         #F26522   /* Nagad orange */
--color-rocket:        #8C3494   /* Rocket purple */

/* Confidence gradient */
--color-confidence-high:   #3FB950
--color-confidence-medium: #D29922
--color-confidence-low:    #F85149
--color-confidence-unknown:#484F58
```

**Aesthetic risk / signature element:** Provider balances are displayed in columns with a subtle left-border stripe in the provider's brand color. This creates an immediately legible "provider lane" metaphor — the platform is one view, but the money is always visually separated. This is the single most memorable UI decision and it directly embodies the platform's core constraint.

### 1.2 Typography

```
Display / Headings:  "Inter"  — weights 600, 700 only; tight tracking (-0.02em)
Body / UI:           "Inter"  — weight 400, 500
Monospace / Data:    "JetBrains Mono" or "Fira Code" — for amounts, IDs, timestamps
```

**Type scale:**
```
--text-xs:   11px / 1.4  — badges, fine metadata
--text-sm:   13px / 1.5  — table cells, secondary labels
--text-base: 15px / 1.6  — body, form fields
--text-md:   17px / 1.4  — card titles, section headers
--text-lg:   21px / 1.3  — page titles
--text-xl:   28px / 1.2  — balance amounts (hero numbers)
--text-2xl:  38px / 1.1  — dashboard hero stat
```

**Amounts always use monospace.** This is a financial application. Numbers must be vertically alignable and scannable.

### 1.3 Spacing & Layout

```
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

Layout uses a **fixed left sidebar (240px) + content area** pattern. The sidebar collapses to icon-only (56px) on smaller screens. Content area uses a 12-column grid with 24px gutters.

### 1.4 Component Tokens

```
--radius-sm:  4px   /* badges, chips */
--radius-md:  8px   /* cards, inputs */
--radius-lg:  12px  /* modals */

--shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px var(--color-border)
--shadow-elevated: 0 8px 24px rgba(0,0,0,0.5)
```

### 1.5 Data Quality Visual Language

This must be consistent across the entire application:

| Feed State    | Color                  | Icon   | Behavior |
|---------------|------------------------|--------|----------|
| `fresh`       | `--color-success`      | ✓ dot  | Normal display |
| `stale`       | `--color-warning`      | ⚠ dot  | Amber tint on card header |
| `missing`     | `--color-danger`       | ✕ dot  | Grey-out balance value, show "—" |
| `conflicting` | `--color-danger`       | ⚡ dot  | Strikethrough on conflicting value |

Confidence score visual:
- `high (≥0.75)`:   solid green confidence bar
- `medium (0.5–0.74)`: amber bar
- `low (<0.5)`:     red bar, wider projection uncertainty cone

---

## 2. Role-Based Access & Login

### 2.1 Demo Login Screen

Since authentication is simplified to "login with a user," the login page presents a **role selector**, not a credential form.

**Page layout:**
```
┌─────────────────────────────────────────────────────────┐
│                    [Platform Logo]                      │
│          Multi-Provider Liquidity Platform              │
│               bKash · Nagad · Rocket                    │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │         Select your demo role                   │   │
│   │                                                 │   │
│   │  ○  Agent — Dhaka North Outlet (OUTLET-001)    │   │
│   │  ○  Field Officer — bKash, Area 3              │   │
│   │  ○  Area Manager — Nagad, Dhaka Zone           │   │
│   │  ○  Provider Ops — bKash                       │   │
│   │  ○  Provider Ops — Nagad                       │   │
│   │  ○  Risk Analyst — bKash                       │   │
│   │  ○  Management — Aggregate View                │   │
│   │                                                 │   │
│   │           [  Enter Platform  ]                  │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   ⚠ Demo environment · Synthetic data only             │
└─────────────────────────────────────────────────────────┘
```

Each role card shows: role name, scope (provider/area/outlet), and a one-line description of what they can do.

**API call:** `POST /api/v1/auth/demo-login` with `{ "role": "agent", "outlet_id": "..." }`

### 2.2 Role Capability Matrix (What Each Role Sees)

| Feature / Page              | Agent | Field Officer | Area Mgr | Provider Ops | Risk Analyst | Management |
|-----------------------------|:-----:|:-------------:|:--------:|:------------:|:------------:|:----------:|
| Own outlet dashboard        | ✓     | read          | read     | provider slice | provider slice | aggregate |
| All-outlet overview         | —     | area scope    | area+    | provider      | provider      | ✓ full    |
| Transactions list           | own   | area+provider | area+    | own provider  | case-linked   | aggregate |
| Balance history             | own   | area+provider | area+    | own provider  | case-linked   | aggregate |
| Liquidity projections       | own   | area+provider | area+    | own provider  | own provider  | aggregate |
| Anomaly flags               | own   | area+provider | area+    | own provider  | own provider  | aggregate |
| Alerts list                 | own   | area scope    | area+    | own provider  | own provider  | read all  |
| Open case from alert        | —     | ✓             | ✓        | ✓             | ✓             | —         |
| Acknowledge case            | if assigned | ✓       | ✓        | own provider  | —             | —         |
| Escalate case               | —     | ✓             | ✓        | own provider  | —             | —         |
| Add case notes              | if assigned | ✓       | ✓        | own provider  | own provider  | —         |
| Resolve case                | —     | ✓             | ✓        | own provider  | —             | —         |
| Risk review                 | —     | —             | —        | —             | ✓ own provider | —        |
| Simulation controls         | —     | —             | —        | —             | —             | admin only |
| Metrics / validation        | —     | —             | —        | —             | read          | ✓ full    |
| Notifications               | own   | assigned      | assigned | assigned      | escalated     | read       |
| Audit events                | own cases | assigned  | assigned | own provider  | own provider  | read all  |
| Data quality panel          | own   | area+provider | area+    | own provider  | own provider  | aggregate |

---

## 3. Application Shell

### 3.1 Sidebar Navigation

The sidebar is fixed left, 240px wide. It contains:

**Header (top):**
- Platform logo mark + wordmark
- Role badge (pill with role name + provider/scope)
- Outlet/scope name in secondary text

**Navigation items** (role-filtered, see section 3.2):
- Dashboard
- Outlets (for non-agent roles)
- Liquidity
- Anomalies
- Alerts
- Cases
- Notifications (with unread badge)
- Transactions
- Data Quality
- Scenarios / Simulation (admin/management only)
- Metrics & Validation (management/risk)
- Audit Log

**Footer:**
- Current user display name
- Locale toggle (EN / বাংলা / Banglish)
- Sign out / Switch Role button

### 3.2 Sidebar Items by Role

```
Agent:           Dashboard, Alerts, Cases, Notifications, Transactions, Data Quality
Field Officer:   Dashboard, Outlets, Alerts, Cases, Notifications, Transactions, Data Quality, Audit
Area Manager:    Dashboard, Outlets, Alerts, Cases, Notifications, Transactions, Data Quality, Audit
Provider Ops:    Dashboard, Outlets, Alerts, Cases, Notifications, Transactions, Data Quality
Risk Analyst:    Dashboard, Alerts, Cases, Anomalies, Liquidity, Metrics, Audit
Management:      Dashboard, Outlets, Alerts, Cases, Liquidity, Anomalies, Metrics, Scenarios, Audit
```

### 3.3 Top Bar

Fixed top bar, 56px tall:
- **Left:** Page title (breadcrumb for nested pages)
- **Center:** Global search (placeholder for stretch)
- **Right:** Data health summary pill (shows worst feed status across visible scope) + Notification bell (unread count) + role avatar

### 3.4 Persistent Data Health Banner

A slim 32px banner directly below the top bar that shows the overall data health status for the current scope. Only visible when at least one feed is not `fresh`.

Examples:
- `⚠ bKash feed stale (12 min) — projections less certain`
- `✕ Nagad feed missing — balance showing last known value`
- `⚡ Rocket feed conflicting — confidence reduced`

This directly maps to the Data Quality Engine's output and ensures users never miss degraded data states.

---

## 4. Page Specifications

---

### Page 1: Dashboard (Agent / Primary Landing Page)

**Route:** `/dashboard` or `/outlets/:outletId/dashboard`
**API:** `GET /api/v1/outlets/{outletId}/dashboard`
**Roles that land here:** All roles (scoped differently)

This is the most important page. It must tell the complete story of one outlet's financial state at a glance.

#### Layout:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: "Dashboard — OUTLET-001, Dhaka North"                 [health] [🔔] │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SHARED CASH                                  LAST UPDATED: 08:01 AM        │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  💵 Shared Physical Cash                               FRESH ●        │   │
│  │  BDT 85,000.00                                                        │   │
│  │  Projection: No shortage within forecast window  ████████ 82% conf   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  PROVIDER BALANCES  (logically separate — never summed)                      │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ │
│  │ │ bKash              │ │ │ Nagad               │ │ │ Rocket             │ │
│  │ ●──────────────────  │ │ ●──────────────────  │ │ ●─────────────────  │ │
│  │ BDT 42,000          │ │ BDT 31,000           │ │ BDT 18,500         │ │
│  │ ⚠ Shortage in ~2h  │ │ FRESH ●              │ │ STALE ⚠ (12 min)   │ │
│  │ ████ 78% conf       │ │ No shortage          │ │ ░░░░ 45% conf       │ │
│  │ [View Projection]   │ │ [View Projection]    │ │ [View Projection]   │ │
│  └──────────────────────┘ └──────────────────────┘ └──────────────────────┘ │
│                                                                              │
│  ACTIVE ALERTS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔴 HIGH  bKash · Liquidity Pressure  Detected 08:01 AM    [View Case]  │ │
│  │  Shared cash falling; bKash cash-outs spiked in last 12 min            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  RECENT TRANSACTIONS (last 10)              [View All Transactions →]        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Time     │ Type      │ Provider │ Amount      │ Status                  │ │
│  │ 08:00    │ Cash-out  │ bKash   │ BDT 1,000  │ ● Completed             │ │
│  │ 07:58    │ Cash-in   │ Nagad   │ BDT 3,500  │ ● Completed             │ │
│  │ ...                                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Key UX Rules:
- **Provider cards use left-border stripe** in provider brand color (bKash magenta, Nagad orange, Rocket purple)
- Balance amounts are **large, monospace, immediately readable**
- Shortage projection shows: time-to-shortage estimate + confidence bar + confidence % + a "less certain" note if feed is stale
- **No aggregate total is ever shown.** The shared cash card and three provider cards are always separate. Add a visible label: "Provider balances are logically separate — totals are not shown"
- Alert strip at bottom: shows only open/unacknowledged alerts for this outlet. Each has severity color, provider chip, age, and a direct "View Case" link
- Transactions table: sortable by time, filterable by provider and type
- If any provider balance is `missing`, show "—" in grey with a tooltip: "Feed not available · Showing last known value from [timestamp]"

---

### Page 2: Outlets Overview (Operations / Management)

**Route:** `/outlets`
**API:** `GET /api/v1/outlets` + per-outlet dashboard summary
**Roles:** Field Officer, Area Manager, Provider Ops, Management

A multi-row table/grid showing all authorized outlets and their health at a glance.

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Outlets  ·  Dhaka Zone, bKash         Filter: [Provider ▾] [Area ▾]    │
├──────────────────────────────────────────────────────────────────────────┤
│  OUTLET        │ SHARED CASH   │ bKash        │ FEED  │ ALERTS │ STATUS  │
│  OUTLET-001    │ BDT 85,000   │ ⚠ Low 42K   │ FRESH │ 1 High │ ● Active│
│  OUTLET-002    │ BDT 120,000  │ OK 91K       │ STALE │ —      │ ● Active│
│  OUTLET-003    │ BDT 22,000   │ CRITICAL 8K  │ FRESH │ 2 High │ ● Active│
│  ...                                                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

- Each row clickable → goes to that outlet's dashboard
- Provider columns are scope-filtered: Provider Ops for bKash only sees bKash column
- ALERTS column shows count by severity (critical first)
- Color-code SHARED CASH by adequacy (green/amber/red based on burn rate)
- Filter chips for provider, area, status, alert-severity
- Sortable: by shared cash, shortage risk, alert count

---

### Page 3: Liquidity Projections

**Route:** `/outlets/:outletId/liquidity` or `/liquidity` (for ops)
**API:** `GET /api/v1/outlets/{outletId}/liquidity-projections`
**Roles:** All (scoped)

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Liquidity — OUTLET-001                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│  [Shared Cash]  [bKash]  [Nagad]  [Rocket]   ← tab switcher            │
│                                                                          │
│  CURRENT STATE                    PROJECTION                             │
│  Balance:  BDT 42,000            Shortage at: ~10:10 AM (2h 9min)      │
│  Burn rate: ~325 BDT/min         Confidence:  ████░░ 78% (medium)       │
│                                  Feed status: FRESH                     │
│                                                                          │
│  CONTRIBUTING SIGNALS                                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ • Cash-out velocity: 6.2/hr (↑ 40% vs 7d avg)                  │   │
│  │ • Cash-in rate: 1.1/hr (within normal range)                    │   │
│  │ • Net depletion: ~325 BDT/min                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  TIME SERIES CHART  (balance over time with projected cone)             │
│  [Chart area — balance line drops, shade widens to show uncertainty]    │
│                                                                          │
│  BALANCE HISTORY  [Last 24h ▾]                                          │
│  [Table: time, balance, change, source]                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Key UX Rules:
- **Confidence cone visualization:** project the balance line forward, then draw a shaded cone that widens as confidence decreases. High confidence = narrow cone. Low/stale = very wide cone + amber/red shading
- If feed is stale/missing: show banner inside the chart: "⚠ Nagad feed stale — projection based on last data at 07:49 AM"
- "Shortage at" time is highlighted in red if within 3 hours, amber if within 6 hours
- Contributing signals are plain-language, no jargon
- Tab switcher lets users flip between shared cash and each provider — never blending them

---

### Page 4: Anomaly Flags

**Route:** `/outlets/:outletId/anomalies` or `/anomalies`
**API:** `GET /api/v1/outlets/{outletId}/anomaly-flags`, `GET /api/v1/anomaly-flags/{flagId}`
**Roles:** Field Officer, Area Manager, Provider Ops, Risk Analyst, Management

#### Layout — List View:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Anomaly Flags  ·  OUTLET-001, bKash     Filter: [Provider] [Status]    │
├──────────────────────────────────────────────────────────────────────────┤
│  SEVERITY │ PROVIDER │ TYPE                    │ DETECTED  │ CONFIDENCE  │
│  🔴 HIGH  │ bKash   │ Near-identical amounts  │ 08:01 AM  │ ████░ 74%  │
│                      5 cash-outs ~BDT 1,000 from 3 accounts in 12 min   │
│                      [View Evidence]  [Open Case]                        │
├──────────────────────────────────────────────────────────────────────────┤
│  🟡 MED   │ Nagad   │ Velocity spike           │ 07:45 AM  │ ███░░ 61%  │
│                      Transaction rate 3× normal between 07:30–07:45     │
│                      [View Evidence]  [Open Case]                        │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Layout — Evidence Detail View:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Back to Anomalies                                                      │
│ Anomaly FLAG-001 · bKash · Near-identical cash-outs  🔴 HIGH             │
│ Detected: 08:01 AM · Confidence: 74% (medium)                           │
├──────────────────────────────────────────────────────────────────────────┤
│  WHAT WAS DETECTED                                                       │
│  5 cash-out transactions with near-identical amounts (≈BDT 1,000)       │
│  from 3 distinct synthetic accounts within a 12-minute window.          │
│                                                                          │
│  EVIDENCE TRANSACTIONS                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Time    │ Amount      │ Account ref      │ Type      │ Status       │  │
│  │ 07:49   │ BDT 1,000  │ PARTY-a1b2      │ Cash-out  │ Completed   │  │
│  │ 07:51   │ BDT 1,000  │ PARTY-c3d4      │ Cash-out  │ Completed   │  │
│  │ 07:52   │ BDT 1,020  │ PARTY-e5f6      │ Cash-out  │ Completed   │  │
│  │ 07:53   │ BDT 1,000  │ PARTY-a1b2      │ Cash-out  │ Completed   │  │
│  │ 07:55   │ BDT 990    │ PARTY-g7h8      │ Cash-out  │ Completed   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  PLAUSIBLE BENIGN EXPLANATION                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ ℹ This pattern may reflect normal pre-Eid demand where multiple   │  │
│  │   customers withdraw similar amounts for household expenses.       │  │
│  │   Human review is required before any conclusion is drawn.        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  UNCERTAINTY                                                             │
│  Confidence reduced slightly due to bKash feed being received 4 minutes │
│  late. Pattern is consistent with known seasonal demand spikes.         │
│                                                                          │
│  [Open Case from this Flag]      Case: CASE-043 (already linked)        │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Key UX Rules:
- **Never use the word "fraud."** Copy always says "unusual pattern," "requires review," "advisory"
- Benign explanation is always shown, never hidden behind a toggle
- Evidence transaction list uses only synthetic party refs (PARTY-xxxxx), never real account info
- Confidence score shown as both a filled bar and a numeric percentage
- "Open Case" button is visible to authorized roles only (not agent-only views)

---

### Page 5: Alerts

**Route:** `/alerts`
**API:** `GET /api/v1/alerts`, `GET /api/v1/alerts/{alertId}`, `GET /api/v1/alerts/{alertId}/explanations`
**Roles:** All (scoped)

#### Layout — List View:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Alerts                         Filter: [Provider] [Severity] [Status]  │
├──────────────────────────────────────────────────────────────────────────┤
│  🔴  HIGH · COMBINED · bKash                            08:01 AM         │
│       Liquidity pressure + unusual activity — OUTLET-001                │
│       Confidence: 74%  ·  Case: CASE-043  [View →]                     │
│─────────────────────────────────────────────────────────────────────────│
│  🟡  MED  · LIQUIDITY · Nagad                           07:45 AM         │
│       Projected shortage in ~4.5h — OUTLET-001                         │
│       Confidence: 61%  ·  No case yet  [Open Case]                     │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Layout — Alert Detail:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Alert ALERT-001 · bKash · COMBINED · 🔴 HIGH                            │
│ Detected: 08:01 AM · Outlet: OUTLET-001                                │
│                                                                          │
│  EXPLANATION                         [EN]  [বাংলা]  [Banglish]         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Situation:   Possible liquidity pressure requires review.       │   │
│  │  Evidence:    5 cash-outs of approx. BDT 1,000 in 12 minutes    │   │
│  │               while shared cash was falling at ~325 BDT/min.    │   │
│  │  Uncertainty: Pattern may be caused by normal pre-Eid demand.   │   │
│  │  Next step:   Review the transactions before coordinating        │   │
│  │               operational support.                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  CONFIDENCE: ████░░  74% (medium) · Feed: FRESH                        │
│                                                                          │
│  LINKED EVIDENCE                                                         │
│  • Liquidity projection: bKash shortage ~10:10 AM  [View]              │
│  • Anomaly flag: Near-identical cash-outs  [View Evidence]              │
│                                                                          │
│  CASE STATUS                                                             │
│  CASE-043 · open → acknowledged · Owner: Field Officer (bKash, Area 3) │
│  [View Full Case →]                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Key UX Rules:
- **Locale toggle (EN / বাংলা / Banglish)** is a 3-state toggle visible on every alert detail
- When Bangla is selected, the explanation text switches to the pre-rendered Bengali explanation from the backend
- **Alert text is read-only and immutable** — no edit button ever appears
- "Next step" is always advisory, never a command
- Provider-scoped users: alerts from other providers do not appear (404 pattern enforced in UI — if a URL is manually typed, show "Alert not found" rather than "Access denied" to avoid provider inference)

---

### Page 6: Cases (Work Queue)

**Route:** `/cases`
**API:** `GET /api/v1/cases`
**Roles:** All except pure agent-only (agents see assigned cases only)

This is the operational heart of the coordination workflow.

#### Layout — List View:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Cases                   My Queue  |  All Cases    Filter: [Status] [▾]  │
├──────────────────────────────────────────────────────────────────────────┤
│  Status      │ Severity │ Provider │ Outlet     │ Owner          │ Age   │
│  🟠 open     │ 🔴 HIGH  │ bKash   │ OUTLET-001 │ Unassigned     │ 2m    │
│  🔵 ack'd    │ 🟡 MED   │ Nagad   │ OUTLET-003 │ Field Officer  │ 18m   │
│  🟣 escalated│ 🔴 HIGH  │ bKash   │ OUTLET-002 │ Risk Analyst   │ 45m   │
│  ✅ resolved │ 🟡 MED   │ Rocket  │ OUTLET-001 │ Area Manager   │ 2h    │
└──────────────────────────────────────────────────────────────────────────┘
```

Status color coding:
- `open` → amber dot
- `acknowledged` → blue dot
- `escalated` → purple dot
- `resolved` → green dot

#### Layout — Case Detail:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Cases   CASE-043 · bKash · OUTLET-001 · 🔴 HIGH                      │
│                                                                          │
│  STATUS: acknowledged  ·  Owner: Field Officer (bKash, Area 3)         │
│  Opened: 08:01 AM  ·  Last action: 08:03 AM (Acknowledged by J. Ahmed) │
│                                                                          │
│  RECOMMENDED NEXT STEP                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Review the listed transactions and contact the outlet through    │   │
│  │ the authorized support process.                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  SOURCE ALERT  →  ALERT-001 · bKash · Combined · 🔴 HIGH  [View]       │
│                                                                          │
│  ─────────────────── ACTIONS ──────────────────────────────────────     │
│  [Acknowledge]  [Escalate]  [Add Note]  [Resolve]   (role-filtered)    │
│                                                                          │
│  ─────────────────── CASE TIMELINE ────────────────────────────────     │
│  08:03 AM  J. Ahmed (Field Officer)      Acknowledged case             │
│  08:02 AM  System (Routing Engine)       Assigned to Field Officer,    │
│                                           bKash Area 3                 │
│  08:01 AM  System (Analytics Engine)     Case opened from ALERT-001    │
│                                                                          │
│  ─────────────────── CASE NOTES ───────────────────────────────────     │
│  08:04 AM  J. Ahmed:  "Contacted outlet. Agent confirms high demand.   │
│             Will monitor and follow up in 30 min."                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Add a note...                                      [Submit Note] │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ─────────────────── RISK REVIEW (Risk Analyst only) ────────────────  │
│  [Mark: Benign Operational]  [Requires Follow-up]  [Data Quality Issue] │
│  [Confirmed Unusual]  [Inconclusive]                                    │
│  ⚠ Review options are advisory only. This is not a fraud verdict.      │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Key UX Rules:
- **Action buttons are role-filtered at render time.** An agent never sees "Escalate." Provider Ops never sees actions on another provider's case
- Escalate action opens a modal: target role selector + mandatory reason field
- Resolve action opens a modal: mandatory resolution summary field
- Risk review panel is only visible and interactive for Risk Analyst role
- Review options never include "Fraud" as a label
- Case notes are **immutable** — once submitted, no edit/delete button appears
- The timeline is chronological (oldest at bottom or newest at top — choose one and be consistent; recommend newest at top for operational efficiency)
- Provider boundary: if a user tries to access a case from another provider by URL, the UI returns the same "Case not found" state as a genuinely missing case

---

### Page 7: Notifications

**Route:** `/notifications`
**API:** `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/read`
**Roles:** All

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Notifications                                     [Mark all read]      │
├──────────────────────────────────────────────────────────────────────────┤
│  ● New case assigned to you                               08:02 AM      │
│    CASE-043 · bKash · OUTLET-001 · 🔴 HIGH              [View Case →]   │
│─────────────────────────────────────────────────────────────────────────│
│  ● Case CASE-041 escalated — needs your review            07:50 AM      │
│    Escalated by Field Officer · Nagad · OUTLET-003       [View Case →]  │
│─────────────────────────────────────────────────────────────────────────│
│    CASE-039 resolved                                      Yesterday      │
│    Resolved by Area Manager · bKash · OUTLET-002         [View Case →]  │
└──────────────────────────────────────────────────────────────────────────┘
```

- Unread notifications have filled dot + slightly elevated background
- Clicking a notification marks it read and navigates to the case
- Bell icon in the top bar shows unread count (badge, max "99+")

---

### Page 8: Transactions

**Route:** `/outlets/:outletId/transactions`
**API:** `GET /api/v1/outlets/{outletId}/transactions`
**Roles:** Agent (own), Field/Area Ops (area+provider scoped), Management (aggregate)

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Transactions · OUTLET-001        Filter: [Provider] [Type] [Date] [▾]  │
│  Showing 847 transactions                                   [Export CSV] │
├──────────────────────────────────────────────────────────────────────────┤
│  Time     │ Type      │ Provider │ Amount      │ Party ref  │ Status     │
│  08:00    │ Cash-out  │ bKash   │ BDT 1,000  │ PARTY-a1b2 │ Completed  │
│  07:58    │ Cash-in   │ Nagad   │ BDT 3,500  │ PARTY-c3d4 │ Completed  │
│  07:55    │ Cash-out  │ bKash   │ BDT 990    │ PARTY-g7h8 │ Completed  │
│  07:52    │ Cash-out  │ bKash   │ BDT 1,020  │ PARTY-e5f6 │ Completed  │
│  ...                                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│  Page 1 of 85                                       [← Prev]  [Next →]  │
└──────────────────────────────────────────────────────────────────────────┘
```

- Provider column has colored chip (bKash = magenta chip, etc.)
- Party refs are always synthetic (PARTY-xxxxx) — no real account numbers
- Flagged transactions (linked to anomaly flag) show a ⚑ icon with hover tooltip
- Filters: provider multi-select, type (cash-in/cash-out/balance-snapshot), date range, amount range
- Pagination, not infinite scroll (for large datasets this is more performant and auditable)

---

### Page 9: Data Quality

**Route:** `/outlets/:outletId/data-quality`
**API:** `GET /api/v1/outlets/{outletId}/data-quality`, `GET /api/v1/outlets/{outletId}/data-quality/history`
**Roles:** All (scoped)

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Data Quality · OUTLET-001                                               │
├──────────────────────────────────────────────────────────────────────────┤
│  CURRENT FEED STATUS                                                     │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
│  │ bKash              │  │ Nagad               │  │ Rocket             │  │
│  │ ● FRESH            │  │ ⚠ STALE             │  │ ✕ MISSING          │  │
│  │ Last: 08:01 AM     │  │ Last: 07:49 AM      │  │ Last: 07:30 AM     │  │
│  │ Conf modifier: 1.0 │  │ Conf modifier: 0.75 │  │ Conf modifier: 0.0 │  │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘  │
│                                                                          │
│  HOW THIS AFFECTS ANALYTICS                                              │
│  • bKash projections: full confidence (feed fresh)                      │
│  • Nagad projections: reduced confidence (⚠ stale feed)                │
│  • Rocket projections: not available (✕ feed missing)                  │
│                                                                          │
│  QUALITY HISTORY  [Last 24h ▾]                                          │
│  [Timeline chart — each provider shown as horizontal lane with colored  │
│   segments: green=fresh, amber=stale, red=missing, flash=conflicting]  │
│                                                                          │
│  ISSUE LOG                                                               │
│  08:01  Nagad feed: 12-min delay detected                               │
│  07:31  Rocket feed: missing — no batch received                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### Page 10: Scenarios / Simulation Control (Management / Admin)

**Route:** `/scenarios`
**API:** Simulation endpoints
**Roles:** Management (demo scenarios), Admin (fault injection)

This page is the demo control panel — critical for the hackathon presentation.

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Demo Scenarios & Simulation Control                                     │
│  ⚠ Simulation environment · All data is synthetic                       │
├──────────────────────────────────────────────────────────────────────────┤
│  SCENARIOS                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ [Run Scenario A] Hidden Provider Shortage                        │   │
│  │  bKash balance depletes while aggregate appears healthy          │   │
│  │─────────────────────────────────────────────────────────────────│   │
│  │ [Run Scenario B] Liquidity Pressure + Unusual Activity           │   │
│  │  Falling cash + near-identical repeated transactions             │   │
│  │─────────────────────────────────────────────────────────────────│   │
│  │ [Run Scenario C] Data Inconsistency                              │   │
│  │  Delayed/conflicting feeds reduce confidence                     │   │
│  │─────────────────────────────────────────────────────────────────│   │
│  │ [Run Scenario D] Coordinated Response                            │   │
│  │  Alert → route → acknowledge → escalate → resolve               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  FAULT INJECTION                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ bKash feed delay     [Enable]  ●──────── OFF                    │   │
│  │ Nagad feed missing   [Enable]  ●──────── OFF                    │   │
│  │ Rocket conflicting   [Enable]  ●──────── OFF                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ACTIVE RUN                                                              │
│  Run ID: RUN-003 · Scenario B · Started: 08:00 AM · Status: Running    │
│  [Reset Run]                                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

- Each scenario button triggers the backend run and **auto-navigates** to the Dashboard to show the result live
- Fault toggles are instant (PATCH endpoint) and the top-bar health banner updates within seconds
- Reset button is clearly destructive (shows confirmation modal)

---

### Page 11: Metrics & Validation (Management / Risk Analyst)

**Route:** `/metrics`
**API:** `GET /metrics`, `GET /api/v1/validation/results`
**Roles:** Management, Risk Analyst

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Validation Evidence & System Metrics                                    │
├──────────────────────────────────────────────────────────────────────────┤
│  ANALYTICS METRICS (held-out evaluation)                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ Anomaly        │  │ Anomaly        │  │ False Positive  │            │
│  │ Precision      │  │ Recall         │  │ Rate            │            │
│  │ 91.3%          │  │ 88.7%          │  │ 8.2%            │            │
│  │ (held-out A/B) │  │ (held-out A/B) │  │ (normal demand) │            │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
│  ┌─────────────────────────────┐  ┌───────────────────────────────┐     │
│  │ Shortage Lead Time          │  │ Alert Explanation Coverage     │     │
│  │ 127 min avg                 │  │ 100% (all alerts have evidence │     │
│  │ (Scenario A, held-out)      │  │  + uncertainty text)          │     │
│  └─────────────────────────────┘  └───────────────────────────────┘     │
│                                                                          │
│  PERFORMANCE METRICS (live)                                              │
│  API avg latency: 48ms    ·    P95 latency: 112ms                       │
│  Data quality incident rate: 2/hr (simulated)                           │
│                                                                          │
│  RELIABILITY                                                             │
│  Audit completeness: 100% (all lifecycle events logged)                 │
│  Provider denial rate: 100% (cross-provider access rejected correctly)  │
│  Idempotency: ✓ verified                                                │
│                                                                          │
│  ─────── METHODOLOGY NOTE ─────────────────────────────────────────     │
│  Metrics measured on held-out synthetic data split.                     │
│  Sample: 300 transactions (Scenarios A/B/C seeds, fixed seed=42).      │
│  Anomaly rule: near-identical amounts, 15-min window, 1 provider.      │
│  Limitations: single rule, synthetic only, not production-validated.   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### Page 12: Audit Log

**Route:** `/cases/:caseId/audit` or `/audit`
**API:** `GET /api/v1/cases/{caseId}/audit-events`
**Roles:** Field Officer (assigned cases), Area Manager, Provider Ops, Risk Analyst, Management

#### Layout:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Audit Log · CASE-043                                                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Time        │ Actor              │ Action         │ Detail               │
│  08:05 AM    │ Risk Analyst (bK) │ review_added   │ "Requires follow-up" │
│  08:04 AM    │ J. Ahmed (FO)     │ note_added     │ "Contacted outlet…"  │
│  08:03 AM    │ J. Ahmed (FO)     │ acknowledged   │ open → acknowledged  │
│  08:02 AM    │ Routing Engine    │ assigned       │ → Field Officer, A3  │
│  08:01 AM    │ Analytics Engine  │ case_opened    │ from ALERT-001       │
└──────────────────────────────────────────────────────────────────────────┘
```

- Audit rows are read-only — no actions in this view
- Actor type distinguishes system actors from human actors visually (system actors in muted text)
- Export as JSON for presentation evidence

---

## 5. Component Library

### 5.1 Core Components

**BalanceCard**
Props: `provider`, `balance`, `feedStatus`, `projection`, `confidenceScore`
Shows: provider color stripe, balance amount (monospace), feed health dot, shortage warning if applicable, confidence bar

**ConfidenceBar**
Props: `score`, `level`, `showLabel`
Visual: filled horizontal bar, color by level, numeric label

**AlertStrip**
Props: `alerts[]`
Shows: severity icon, provider chip, age, action link

**CaseBadge**
Props: `status`
Shows: colored dot + status label

**FeedStatusDot**
Props: `status` (`fresh` | `stale` | `missing` | `conflicting`)
Shows: colored dot with tooltip on hover

**LocaleToggle**
Props: `current`, `onChange`
Shows: 3-button toggle `EN | বাং | BNG`

**ActionButton**
Props: `action`, `caseId`, `disabled`, `requiredRole`
Shows: role-filtered; if `disabled` shows tooltip explaining why

**ProviderChip**
Props: `provider`
Shows: colored pill (bKash=magenta, Nagad=orange, Rocket=purple)

**TimelineEntry**
Props: `timestamp`, `actor`, `actorType`, `action`, `detail`
Shows: dot on vertical line, actor name, action badge, detail text

**ConfidenceConeChart**
Props: `history[]`, `projection`, `confidence`, `feedStatus`
Shows: SVG line chart with projected shaded cone, narrower for high confidence

### 5.2 Loading & Empty States

Every data-fetching component has explicit states:

- **Loading:** skeleton shimmer (not a spinner) — shimmer that matches the shape of the data
- **Empty:** descriptive message + action link ("No alerts in your scope — the outlet appears healthy")
- **Error:** "Could not load data — [Retry]" — never expose error codes to end users
- **Forbidden:** "Not found" — same as 404, never "Access denied" (protects provider boundary)
- **Degraded:** shown inline within components when data is stale/missing

### 5.3 Modals

All case actions use modals (not page navigation) to keep context:

- **Acknowledge:** confirmation text + optional note field
- **Escalate:** target role dropdown (filtered by authorized routing) + mandatory reason text
- **Resolve:** mandatory resolution summary text + confirmation
- **Add Note:** text area + submit
- **Open Case:** confirmation that shows the alert summary + routing preview ("This will be assigned to Field Officer, bKash Area 3")

---

## 6. Navigation & Page Routing

```
/                         → redirect to /dashboard
/login                    → Demo role selector
/dashboard                → Outlet dashboard (agent = own outlet; ops = overview)
/outlets                  → Outlets overview (ops/management only)
/outlets/:id              → Specific outlet dashboard
/outlets/:id/liquidity    → Liquidity projections for outlet
/outlets/:id/anomalies    → Anomaly flags for outlet
/outlets/:id/transactions → Transaction history
/outlets/:id/data-quality → Feed health detail
/alerts                   → Alert work queue
/alerts/:id               → Alert detail with explanation
/cases                    → Case work queue
/cases/:id                → Case detail + timeline + actions
/notifications            → Notification inbox
/scenarios                → Simulation control (management/admin)
/metrics                  → Validation & observability (management/risk)
/audit                    → Case audit log (accessible from case detail)
```

**Route guards:** All routes except `/login` check the active role from the in-memory session. Unauthorized routes show the same "not found" page, not a "forbidden" page.

---

## 7. Real-Time / Polling Strategy

The backend does not specify WebSockets, so use **polling** with sensible intervals:

| Data Type | Poll Interval | Rationale |
|-----------|--------------|-----------|
| Dashboard balances + projections | 30 seconds | Feeds arrive in batches; sub-30s is wasteful |
| Active alerts | 30 seconds | Alert detection runs on feed events |
| Notifications | 15 seconds | Case assignments are time-sensitive |
| Case status | On-focus (tab refocus) | Collaborative editing risk |
| Data quality | 30 seconds | Mirrors feed cadence |
| Simulation run status | 5 seconds (while run active) | Demo scenario needs live feedback |

Show a "Last updated X seconds ago" label on each page. Clicking it forces a refresh.

---

## 8. Locale / Language Implementation

Three explanation locales are togglable on Alert Detail and Case Source sections:

- **EN (English):** Default. Always available.
- **বাংলা (Bangla):** Pre-rendered from backend, served via `GET /api/v1/alerts/{id}/explanations?locale=bn`
- **Banglish:** Latin-script Bengali, same endpoint with `locale=banglish`

**Implementation notes:**
- Locale toggle remembers selection for the session (stored in React state, not localStorage)
- Falls back to English if the requested locale render is not available
- User's preferred locale from `/api/v1/me/preferences` sets the initial toggle state
- `PATCH /api/v1/me/preferences` saves the preference when the user changes it
- The rest of the UI always stays in English — only the alert/case explanation text switches

---

## 9. Provider Boundary Enforcement (UI Layer)

These rules supplement the backend's RBAC:

1. **Provider chips on every data element** — always visible so the user knows which provider's data they're looking at
2. **Filtered lists** — the API already scopes, but the UI must never show an "empty" state that implies a record exists but is hidden. Always show zero results as "no results in your scope"
3. **URL safety** — if a user manually types a case or alert URL that belongs to another provider, the UI calls the API, gets a 404, and shows the standard "not found" state — no error that reveals the record exists
4. **No cross-provider comparison UI** — do not build any UI that places Provider A and Provider B financial data side by side in a way that could infer one from the other

---

## 10. Responsible Design Signals in the UI

Several UI elements must actively reinforce responsible design constraints:

- **No "Fraud" label** anywhere in the UI — use "unusual pattern," "requires review," "flag for follow-up"
- **Advisory banner on anomaly pages:** "These signals are advisory only. No account action or accusation results from this review."
- **Benign explanation always shown** with anomaly evidence — never hidden
- **"No automatic action" footer on case actions** — e.g., "Resolving this case records a workflow outcome. No financial action is taken."
- **Simulation environment banner** — visible on all pages in demo mode: "⚠ Demo environment · Synthetic data only · No real accounts or funds involved"

---

## 11. Tech Stack Recommendation

| Layer | Choice | Rationale |
|---|---|---|
| Framework | React 18 + Vite | Fast dev server, small bundle, component model fits role-based views |
| Routing | React Router v6 | File-based routing pattern, easy route guards |
| State | Zustand or React Query | React Query for server state (caching, polling, stale-while-revalidate); Zustand for session/role |
| Styling | Tailwind CSS | Utility-first maps well to the token system above; no CSS-in-JS overhead |
| Charts | Recharts | Lightweight, composable, integrates well with React |
| Icons | Lucide React | Clean, consistent, open license |
| Tables | TanStack Table v8 | Headless, handles sorting/filtering/pagination |
| HTTP client | Axios or native fetch + React Query | React Query handles caching and polling |

---

## 12. Implementation Priority Order

Given the hackathon context, build in this order:

**Phase 1 (Core story):**
1. Login / Role selector
2. App shell (sidebar, top bar, role context)
3. Agent Dashboard (the one page that tells the complete story)
4. Alert Detail with locale toggle

**Phase 2 (Coordination workflow):**
5. Cases list + Case detail (with all action modals)
6. Notifications

**Phase 3 (Intelligence depth):**
7. Liquidity projections page with confidence cone chart
8. Anomaly flags list + evidence detail

**Phase 4 (Operational depth):**
9. Transactions list
10. Data Quality page
11. Outlets overview (multi-outlet)

**Phase 5 (Demo & Presentation):**
12. Scenarios / Simulation control page
13. Metrics & Validation page
14. Audit log

**Phase 6 (Polish):**
15. All loading/empty/error states
16. Polling & live data refresh
17. Responsive layout (mobile-friendly sidebar collapse)

---

## 13. Demo Flow Mapping (Scenario A → D)

The UI must support this exact presentation path:

**Scenario A — Hidden Shortage:**
> Login as Agent → Dashboard shows bKash balance low, shortage projected ~2h, confidence 78% → Click "View Projection" → See contributing signals → bKash has fresh feed, Nagad stale (confidence reduced) → Alert strip shows 1 HIGH alert

**Scenario B — Unusual Activity:**
> Login as Field Officer (bKash) → Cases queue shows open HIGH case → Open Case → View source alert with EN explanation → Toggle to বাংলা alert → See anomaly evidence (5 near-identical cash-outs) → Benign explanation shown → Acknowledge case → Add note

**Scenario C — Data Inconsistency:**
> Enable "Nagad delay" fault on Scenarios page → Navigate to Dashboard → Health banner shows "⚠ Nagad feed stale" → Open Nagad projection → Confidence cone is wide, amber → Alert explanation shows uncertainty note → Anomaly for Nagad suppressed ("confidence too low to alert")

**Scenario D — Coordinated Response:**
> Alert created → routed to Field Officer → Notifications badge increments → Open case → Acknowledge → Escalate to Risk Analyst with reason → Risk Analyst logs in → Sees escalated case → Reviews evidence → Adds "Requires follow-up" review → Field Officer resolves with summary → Audit log shows complete chain

---

*End of Frontend Redesign Plan*
*Version 1.0 · July 2026 · Multi-Provider Agent Liquidity & Coordination Platform*
