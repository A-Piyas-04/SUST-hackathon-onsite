# System Diagrams

Multi-Provider Agent Liquidity & Coordination Platform — diagrams derived from the implemented backend (`backend/app/`), schema (`docs/schema.md`), and system design (`docs/System-Design.md`).

> All diagrams use [Mermaid](https://mermaid.js.org/). Render in GitHub, VS Code (Mermaid preview), or any Mermaid-compatible viewer.

---

## 1. Data-Flow Diagram

End-to-end movement of simulated provider data through ingestion, ledger, analytics, alerts, cases, and audit.

```mermaid
flowchart TB
    subgraph External["Simulated Provider Feeds"]
        BK[bKash Feed]
        NG[Nagad Feed]
        RK[Rocket Feed]
    end

    subgraph Simulation["Simulation Layer"]
        SC[Scenario Generator<br/>scenario_a / b / c / d]
        FI[Fault Injection<br/>late / missing / corrupt]
        SR[(simulation_runs)]
    end

    subgraph Ingestion["Ingestion & Normalization"]
        API_ING[POST /api/v1/batches]
        ADP[Provider Adapters<br/>bkash / nagad / rocket shapes]
        NORM[Normalizer]
        IB[(ingestion_batches)]
        IE[(ingestion_events)]
    end

    subgraph Quality["Data Quality"]
        QF[Batch Assessment<br/>quality_foundation]
        QE[Quality Engine<br/>fresh / stale / missing / conflicting]
        DQA[(data_quality_assessments)]
    end

    subgraph Ledger["Ledger & Aggregation"]
        LW[Ledger Writer]
        TXN[(transactions)]
        CBS[(cash_balance_snapshots)]
        PBS[(provider_balance_snapshots)]
        DASH[GET /outlets/{id}/dashboard]
    end

    subgraph Analytics["Analytics Engines"]
        AR[Analytics Runner]
        LE[Liquidity Engine<br/>per-reserve burn rate]
        AE[Anomaly Engine<br/>near_identical_amounts]
        LP[(liquidity_projections)]
        AF[(anomaly_flags)]
        ENV[ResultEnvelope]
        AC[AlertCandidate Adapter]
    end

    subgraph Coordination["Alert & Case Management"]
        PUB[POST /internal/alerts/publish]
        AL[(alerts)]
        EXP[Explanation Renderer<br/>EN / BN / Banglish]
        AE_TBL[(alert_explanations)]
        RT[Routing Engine]
        CS[(cases)]
        NOTIF[(notifications)]
        AUD[(audit_events)]
    end

    subgraph Clients["Role-Based Clients"]
        UI_AGENT[Agent View]
        UI_OPS[Field Officer / Area Manager]
        UI_PROV[Provider Ops]
        UI_RISK[Risk / Management]
    end

    BK & NG & RK --> SC
    SC --> FI
    FI --> API_ING
    SR --> API_ING
    API_ING --> ADP --> NORM
    NORM --> IB & IE
    NORM -->|accepted events| LW
    NORM -->|rejected| IE
    IB --> QF
    QF --> QE
    LW --> TXN & CBS & PBS
    TXN & CBS & PBS --> DASH

    TXN & CBS & PBS --> AR
    QE --> AR
    AR --> LE & AE
    LE --> LP
    AE --> AF
    LE & AE --> ENV --> AC
    DQA --> ENV

    AC --> PUB
    PUB --> AL
    PUB --> EXP --> AE_TBL
    LP & AF & DQA -.->|typed source links| AL
    PUB --> AUD

    AL -->|open case| RT --> CS
    CS --> NOTIF
    CS --> AUD

    DASH --> UI_AGENT & UI_OPS
    AL --> UI_OPS & UI_PROV & UI_RISK
    CS --> UI_OPS & UI_PROV & UI_RISK
    NOTIF --> UI_OPS & UI_PROV & UI_RISK
```

### Degraded-data branch (Scenario C)

```mermaid
flowchart LR
    FAULT[Fault Injection<br/>late / conflicting feed]
    QE[Quality Engine]
    LE[Liquidity Engine]
    AN[Anomaly Engine]
    SUP[Suppress high-confidence<br/>anomaly flags]
    WIDE[Widen confidence band<br/>mark non-actionable]
    UI[Dashboard shows<br/>degraded feed state]

    FAULT --> QE
    QE -->|stale / conflicting| LE --> WIDE
    QE -->|stale / conflicting| AN --> SUP
    WIDE & SUP --> UI
```

---

## 2. Use-Case Diagrams

### 2.1 Platform overview (all actors)

```mermaid
flowchart LR
    subgraph Actors
        AG((Agent))
        FO((Field Officer))
        AM((Area Manager))
        PO((Provider Ops))
        RA((Risk Analyst))
        MG((Management))
        SYS((System / Analytics))
    end

    subgraph UC_Visibility["Unified Visibility"]
        UC1[View outlet dashboard<br/>cash + per-provider balances]
        UC2[Browse transactions<br/>& balance history]
        UC3[Inspect data-quality<br/>health per provider]
    end

    subgraph UC_Intel["Liquidity & Anomaly Intelligence"]
        UC4[Run liquidity forecast<br/>per reserve]
        UC5[Detect unusual patterns<br/>with evidence]
        UC6[View projections & flags]
    end

    subgraph UC_Coord["Coordination & Cases"]
        UC7[Publish alerts from<br/>analytics candidates]
        UC8[Open case from alert]
        UC9[Acknowledge / escalate /<br/>resolve case]
        UC10[Add notes & reviews]
        UC11[Receive in-app<br/>notifications]
    end

    subgraph UC_Sim["Simulation & Demo"]
        UC12[Start simulation run<br/>scenario A–D]
        UC13[Inject faults<br/>for degraded-data demo]
        UC14[Reset run artifacts]
    end

    subgraph UC_Gov["Governance"]
        UC15[Enforce provider<br/>data boundaries]
        UC16[Audit case lifecycle]
        UC17[Read localized<br/>alert explanations]
    end

    AG --> UC1 & UC2 & UC11
    FO & AM --> UC1 & UC2 & UC3 & UC8 & UC9 & UC10 & UC11
    PO --> UC1 & UC6 & UC8 & UC9 & UC10 & UC11 & UC17
    RA --> UC6 & UC8 & UC9 & UC10 & UC16
    MG --> UC1 & UC6 & UC16
    SYS --> UC4 & UC5 & UC7

    AG & FO & AM & PO & RA & MG --> UC15
    FO & AM & PO & RA --> UC12 & UC13 & UC14
```

### 2.2 Agent use cases

```mermaid
flowchart TB
    AG((Agent))

    AG --> UC_DASH[View combined dashboard<br/>shared cash + provider balances]
    AG --> UC_TXN[View recent transactions]
    AG --> UC_NOTIF[Receive case notifications<br/>for own outlet]
    AG --> UC_ACK[Acknowledge assigned cases]
    AG --> UC_NOTE[Add operational notes]

    UC_DASH -.->|read-only| LEDGER[(Ledger)]
    UC_NOTIF -.->|in_app channel| NOTIF[(notifications)]
```

### 2.3 Provider Ops use cases (provider-boundary scoped)

```mermaid
flowchart TB
    PO((Provider Ops<br/>bKash / Nagad / Rocket))

    PO --> UC_ALERTS[List & read alerts<br/>own provider only]
    PO --> UC_CASE[Manage cases<br/>own provider only]
    PO --> UC_EXP[Read explanations<br/>EN / BN / Banglish]
    PO --> UC_ANOM[Review anomaly evidence<br/>& benign context]
    PO --> UC_DENY[Cannot access<br/>other provider cases]

    UC_ALERTS & UC_CASE --> AUTHZ{can_access_scope<br/>provider_id match}
    AUTHZ -->|forbidden| SAFE404[Safe 404<br/>no existence leak]
    AUTHZ -->|allowed| DATA[(alerts / cases)]
```

### 2.4 Operations & risk use cases

```mermaid
flowchart TB
    FO((Field Officer))
    AM((Area Manager))
    RA((Risk Analyst))

    FO & AM --> UC_ROUTE[Cases routed by<br/>provider + area rules]
    FO & AM --> UC_ESC[Escalate to<br/>risk_analyst]
    RA --> UC_REVIEW[Submit case review<br/>false-positive feedback]
    FO & AM & RA --> UC_TIMELINE[View case timeline<br/>& audit trail]
    FO & AM --> UC_ASSIGN[Reassign case owner]

    UC_ROUTE --> RR[(routing_rules)]
    UC_REVIEW --> METRICS[Validation metrics<br/>precision / recall]
```

---

## 3. Sequence Diagrams

### 3.1 Simulation run → ingestion → ledger

Triggered by `POST /api/v1/runs` or CLI; executes `run_service._execute_run`.

```mermaid
sequenceDiagram
    actor User
    participant API as Simulation API
    participant Gen as Synthetic Generator
    participant Fault as Fault Effects
    participant Ing as Ingestion Pipeline
    participant Norm as Normalizer
    participant Led as Ledger Writer
    participant QF as Quality Foundation
    participant DB as PostgreSQL

    User->>API: POST /runs {scenario, seed}
    API->>DB: INSERT simulation_runs
    API->>Gen: generate_dataset(scenario, seed)
    Gen-->>API: GeneratedBatch[]
    API->>Fault: apply_faults_to_batches(batches, faults)
    Fault-->>API: mutated batches
  loop each provider batch
        API->>Ing: ingest_batch(events)
        Ing->>DB: INSERT ingestion_batches
        loop each event
            Ing->>Norm: normalize_event(provider shape)
            alt valid
                Norm-->>Ing: NormalizedTransaction / Balance
                Ing->>DB: INSERT ingestion_events (normalized)
                Ing->>Led: write_transaction / write_snapshot
                Led->>DB: INSERT transactions / snapshots
            else rejected
                Ing->>DB: INSERT ingestion_events (rejected)
            end
        end
        Ing->>QF: record_batch_assessment
        QF->>DB: INSERT batch quality row
    end
    API-->>User: RunResponse + artifact counts
```

### 3.2 Analytics run → alert publication

Triggered by `POST /api/v1/internal/alerts/publish` or individual analytics endpoints.

```mermaid
sequenceDiagram
    actor Ops as Operator / System
    participant API as Alerts API
    participant Run as Analytics Runner
    participant QE as Quality Engine
    participant LE as Liquidity Engine
    participant AN as Anomaly Engine
    participant Adp as AlertCandidate Adapter
    participant Pub as Alert Publisher
    participant Exp as Explanations
    participant DB as PostgreSQL

    Ops->>API: POST /internal/alerts/publish {run_id}
    API->>Run: run_liquidity(run_id)
    Run->>DB: read cash + provider observations
    Run->>QE: assess_provider_quality (per provider + shared cash)
    QE-->>Run: confidence_modifier, status
    Run->>LE: forecast_reserve (per reserve, never blended)
    LE-->>Run: LiquidityForecast
    Run->>DB: INSERT analytics_runs, projections, assessments
    Run->>Adp: envelope_to_alert_candidate
    Adp-->>Run: AlertCandidate[] (actionable only)

    API->>Run: run_anomalies(run_id)
    Run->>AN: detect_near_identical_amounts
    alt data quality degraded
        AN-->>Run: suppressed / low confidence
    else pattern detected
        AN-->>Run: requires_review + evidence
    end
    Run->>DB: INSERT anomaly_flags
    Run->>Adp: envelope_to_alert_candidate

    loop each candidate
        Pub->>DB: check dedup_key (run-scoped)
        alt duplicate active alert
            Pub-->>API: deduplicated_alert_id
        else new
            Pub->>DB: INSERT alerts + source links
            Pub->>Exp: render_and_persist (en, bn, bn_latn)
            Exp->>DB: INSERT alert_explanations
            Pub->>DB: INSERT audit_events (alert_published)
        end
    end
    API-->>Ops: PublishResponse {published, deduplicated}
```

### 3.3 Case lifecycle & notifications (Scenario D)

```mermaid
sequenceDiagram
    actor User as Stakeholder (JWT)
    participant API as Cases API
    participant Auth as AuthZ (can_access_scope)
    participant Cases as Case Service
    participant Route as Routing Engine
    participant Notif as Notification Queue
    participant Audit as Audit Log
    participant DB as PostgreSQL

    User->>API: POST /alerts/{id}/cases
    API->>Auth: require_alert + scope check
    Auth-->>API: alert row
    API->>Cases: open_case(alert_id)
    Cases->>DB: SELECT existing case (idempotent)
    alt case exists
        Cases-->>API: existing CaseOutput
    else new case
        Cases->>Route: resolve_routing(provider, area, type, severity)
        Route->>DB: match routing_rules (specificity + priority)
        Route-->>Cases: target_role
        Cases->>DB: INSERT cases (status=open)
        Cases->>DB: INSERT case_status_history, case_assignments
        Cases->>Notif: queue_notification(case_opened)
        Cases->>Audit: write_audit_event(case_opened)
    end
    API-->>User: CaseOutput

    User->>API: POST /cases/{id}/acknowledge
    API->>Cases: acknowledge (idempotency_key, version)
    Cases->>DB: UPDATE status → acknowledged (optimistic lock)
    Cases->>Audit: case_acknowledged
    API-->>User: CaseOutput

    opt escalation
        User->>API: POST /cases/{id}/escalate {target_role}
        Cases->>DB: status → escalated, reassign owner
        Cases->>Notif: queue_notification(case_escalated)
        Cases->>Audit: case_escalated
    end

    User->>API: POST /cases/{id}/resolve {summary}
    Cases->>DB: status → resolved
    Cases->>Audit: case_resolved
    API-->>User: CaseOutput

    User->>API: GET /notifications
    API->>Notif: list_notifications (role + scope filter)
    Notif-->>User: queued in-app notifications
```

### 3.4 Dashboard read path

```mermaid
sequenceDiagram
    actor Client
    participant API as Reference API
    participant Auth as AuthZ
    participant Reader as Ledger Reader
    participant DB as PostgreSQL

    Client->>API: GET /outlets/{id}/dashboard
    API->>Auth: verify outlet scope
    API->>Reader: get_dashboard(outlet_id)
    Reader->>DB: cash_balance_snapshots (latest)
    Reader->>DB: provider_balance_snapshots (per account)
    Reader->>DB: latest liquidity_projections (interim)
    Reader->>DB: latest data_quality_assessments
    Reader-->>API: DashboardResponse<br/>(separated reserves, never blended)
    API-->>Client: JSON envelope
```

---

## 4. Alert Coordination Flow Diagram

Full path from detection to human resolution, including routing precedence, legal state transitions, and feedback.

```mermaid
flowchart TB
    START([Analytics detects<br/>actionable signal])

    subgraph Detection["Detection & Candidate Formation"]
        LIQ{Liquidity:<br/>projected shortage<br/>within window?}
        ANO{Anomaly:<br/>near-identical<br/>cluster?}
        DQ{Data quality<br/>allows alert?}
        CAND[Build AlertCandidate<br/>evidence + confidence + dedup_key]
    end

    subgraph Publication["Alert Publication"]
        DEDUP{Active alert with<br/>same run dedup_key?}
        PUB[Persist alert<br/>freeze structured_payload]
        LINK[Link source artifacts<br/>projection / flag / quality IDs]
        RENDER[Render explanations<br/>situation · evidence · uncertainty<br/>next step · benign context]
        AUD1[Audit: alert_published]
    end

    subgraph Routing["Owner Assignment"]
        RULES[(routing_rules)]
        MATCH[Match: provider + area + alert_type<br/>+ minimum_severity]
        SPEC[Win by specificity,<br/>then priority ASC]
        OWNER[Assign current_owner_role<br/>agent / field_officer /<br/>provider_ops / risk_analyst]
    end

    subgraph CaseLifecycle["Case Lifecycle"]
        OPEN((open))
        ACK((acknowledged))
        ESC((escalated))
        RES((resolved))

        OPEN -->|acknowledge| ACK
        OPEN -->|escalate| ESC
        ACK -->|escalate| ESC
        ACK -->|resolve + summary| RES
        ESC -->|resolve + summary| RES
    end

    subgraph HumanActions["Human Actions (advisory only)"]
        VIEW[View alert + explanations<br/>EN / BN / Banglish]
        NOTE[Add case notes]
        ASSIGN[Reassign to user/role]
        REVIEW[Submit review<br/>was_false_positive?]
    end

    subgraph Delivery["Notification Delivery"]
        Q[Queue in_app notification]
        LIST[Recipient lists via<br/>role + provider scope]
        READ[Mark notification read]
    end

    subgraph Feedback["Feedback & Audit"]
        TIMELINE[v_case_timeline view]
        AUDIT[(audit_events<br/>append-only)]
        VAL[Validation metrics<br/>precision / recall / FPR]
    end

    START --> LIQ & ANO
    LIQ & ANO --> DQ
    DQ -->|yes| CAND
    DQ -->|no / suppressed| END_SUPP([Suppressed or<br/>data-quality advisory])
    CAND --> DEDUP
    DEDUP -->|duplicate| END_DEDUP([Return existing<br/>active alert])
    DEDUP -->|new| PUB --> LINK --> RENDER --> AUD1

    AUD1 --> OPEN
    OPEN --> MATCH
    RULES --> MATCH --> SPEC --> OWNER
    OWNER --> Q --> LIST

    OPEN & ACK & ESC --> VIEW & NOTE & ASSIGN
    ESC --> REVIEW
    RES --> REVIEW

    OPEN & ACK & ESC & RES --> TIMELINE
    VIEW & NOTE & ASSIGN & REVIEW --> AUDIT
    REVIEW --> VAL
    LIST --> READ

    style START fill:#e8f4fc
    style RES fill:#e8fce8
    style END_SUPP fill:#fff3e0
    style END_DEDUP fill:#fff3e0
```

### Routing precedence (implementation detail)

Matches `backend/app/services/coordination/routing.py`:

| Step | Rule |
|------|------|
| 1 | Filter active `routing_rules` by `provider_id` (exact or NULL wildcard) |
| 2 | Filter by `area_id` (exact or NULL wildcard) |
| 3 | Filter by `alert_type` (exact or NULL wildcard) |
| 4 | Require alert `severity` ≥ rule `minimum_severity` |
| 5 | Pick highest specificity: provider (+2) + area (+1) |
| 6 | Tie-break: lower `priority` value wins |
| 7 | Fallback: `field_officer` if no rule matches |

### Legal case transitions

Matches `cases.py` and DB trigger in migration 004:

```
open        → acknowledged | escalated
acknowledged → escalated   | resolved
escalated   → resolved
```

Resolution requires prior `acknowledged` or `escalated` status and a `resolution_summary`.

---

## Diagram Index

| # | Diagram | Primary source modules |
|---|---------|------------------------|
| 1 | Data-flow (steady + degraded) | `ingestion/`, `ledger/`, `quality/`, `analytics/`, `coordination/` |
| 2.1–2.4 | Use cases by actor | `api/v1/*`, `core/authz.py`, `contracts/v1/enums.py` |
| 3.1 | Simulation → ledger sequence | `simulation/run_service.py`, `ingestion/pipeline.py` |
| 3.2 | Analytics → alert publish | `analytics/runner.py`, `coordination/alerts.py` |
| 3.3 | Case lifecycle | `coordination/cases.py`, `coordination/notifications.py` |
| 3.4 | Dashboard read | `ledger/reader.py`, `api/v1/reference.py` |
| 4 | Alert coordination flow | `coordination/*`, `alert_candidate_adapter.py` |
