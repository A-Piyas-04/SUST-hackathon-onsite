/**
 * Centralized, typed API client for the Multi-Provider Agent Liquidity &
 * Coordination Platform demo UI (Phase 6).
 *
 * Guardrails reflected here:
 *  - Decision-support only: no transfer/refill/freeze/verdict operations exist.
 *  - Shared physical cash and provider e-money stay separate (see Dashboard types).
 *  - Confidential resources return a uniform safe not-found (404) whether the id
 *    is missing OR forbidden — the client surfaces both as `ApiErrorKind.notFound`
 *    so the UI never leaks the existence of cross-provider records.
 */

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

const API = () => `${getApiBaseUrl()}/api/v1`;

// --------------------------------------------------------------------------- //
// Auth token (browser session)
// --------------------------------------------------------------------------- //
const TOKEN_KEY = "liq_demo_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

// --------------------------------------------------------------------------- //
// Error model
// --------------------------------------------------------------------------- //
export type ApiErrorKind =
  | "unauthorized" // 401 — no/invalid session
  | "forbidden" // 403 — authenticated but action denied
  | "notFound" // 404 — missing OR forbidden confidential resource (safe)
  | "validation" // 422
  | "notImplemented" // 501 (later-phase stub)
  | "server" // 5xx
  | "network" // fetch failed
  | "error"; // anything else

export class ApiError extends Error {
  kind: ApiErrorKind;
  status: number;
  code: string;
  requestId: string | null;

  constructor(
    kind: ApiErrorKind,
    status: number,
    code: string,
    message: string,
    requestId: string | null = null,
  ) {
    super(message);
    this.kind = kind;
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

function kindForStatus(status: number, code: string): ApiErrorKind {
  if (status === 401) return "unauthorized";
  if (status === 403 || code === "forbidden") return "forbidden";
  if (status === 404 || code === "not_found") return "notFound";
  if (status === 422) return "validation";
  if (status === 501) return "notImplemented";
  if (status >= 500) return "server";
  return "error";
}

async function request<T>(
  path: string,
  opts: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API()}${path}`, {
      method,
      headers,
      cache: "no-store",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("network", 0, "network_error", "Unable to reach the backend.");
  }

  if (res.status === 204) return undefined as T;

  let payload: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!res.ok) {
    const err = (payload as { error?: { code?: string; message?: string; request_id?: string } } | null)?.error;
    const code = err?.code ?? "http_error";
    throw new ApiError(
      kindForStatus(res.status, code),
      res.status,
      code,
      err?.message ?? `Request failed (${res.status}).`,
      err?.request_id ?? null,
    );
  }

  return payload as T;
}

// --------------------------------------------------------------------------- //
// Shared enums / primitives
// --------------------------------------------------------------------------- //
export type ProviderCode = "bkash" | "nagad" | "rocket";
export type ReserveType = "shared_cash" | "provider_e_money";
export type ConfidenceLevel = "high" | "medium" | "low" | "unavailable";
export type FeedHealthStatus = "fresh" | "stale" | "missing" | "conflicting";
export type LocaleCode = "en" | "bn" | "bn_latn";
export type CaseStatus = "open" | "acknowledged" | "escalated" | "resolved";
export type AppRole =
  | "agent"
  | "field_officer"
  | "area_manager"
  | "provider_ops"
  | "risk_analyst"
  | "management"
  | "admin";
export type ScenarioCode = "normal" | "scenario_a" | "scenario_b" | "scenario_c" | "scenario_d";
export type AnomalyDisposition =
  | "requires_review"
  | "suppressed_data_quality"
  | "dismissed_benign"
  | "confirmed_unusual"
  | "inconclusive";

// --------------------------------------------------------------------------- //
// Health
// --------------------------------------------------------------------------- //
export type HealthResponse = {
  status: string;
  database: string;
  env: string;
  checked_at: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${getApiBaseUrl()}/health`, { cache: "no-store" });
  if (!res.ok) throw new ApiError("server", res.status, "health_error", "Health check failed.");
  return (await res.json()) as HealthResponse;
}

// --------------------------------------------------------------------------- //
// Auth / principal
// --------------------------------------------------------------------------- //
export type Scope = {
  role: AppRole;
  provider_id: string | null;
  area_id: string | null;
  outlet_id: string | null;
};

export type Principal = {
  user_id: string;
  display_name: string;
  preferred_locale: LocaleCode;
  roles: AppRole[];
  scopes: Scope[];
  permissions: string[];
};

export type DemoLoginResponse = {
  token: string;
  token_type: string;
  user: Principal;
};

/** Friendly demo identities offered in the login/role-switch surface. */
export const DEMO_USERS: { key: string; label: string; role: AppRole; note: string }[] = [
  { key: "agent", label: "Agent (Outlet 001)", role: "agent", note: "Owns one outlet" },
  { key: "area_manager", label: "Field / Area Ops", role: "area_manager", note: "bKash · Market area" },
  { key: "bkash_ops", label: "Provider Ops — bKash", role: "provider_ops", note: "bKash confidential scope" },
  { key: "nagad_ops", label: "Provider Ops — Nagad", role: "provider_ops", note: "Nagad confidential scope" },
  { key: "rocket_ops", label: "Provider Ops — Rocket", role: "provider_ops", note: "Rocket confidential scope" },
  { key: "risk_analyst", label: "Risk Analyst", role: "risk_analyst", note: "bKash risk review" },
  { key: "management", label: "Management", role: "management", note: "Cross-provider oversight" },
  { key: "admin", label: "Demo Admin", role: "admin", note: "Simulation, faults, and publish controls" },
];

export function demoLogin(userKey: string): Promise<DemoLoginResponse> {
  return request<DemoLoginResponse>("/auth/demo-login", {
    method: "POST",
    auth: false,
    body: { user_key: userKey },
  });
}

export function fetchMe(): Promise<Principal> {
  return request<Principal>("/me");
}

export function updatePreferences(locale: LocaleCode): Promise<Principal> {
  return request<Principal>("/me/preferences", { method: "PATCH", body: { preferred_locale: locale } });
}

// --------------------------------------------------------------------------- //
// Reference / ledger / dashboard
// --------------------------------------------------------------------------- //
export type ProviderRef = { provider_id: string; code: ProviderCode; display_name: string };
export type OutletListItem = {
  outlet_id: string;
  synthetic_code: string;
  display_name: string;
  area_name: string;
};

export type ProjectionSummary = {
  shortage_at: string | null;
  confidence_score: string;
  confidence_level: string;
};
export type FeedHealthSummary = { status: FeedHealthStatus; confidence_modifier: number };
export type SharedCashDashboard = {
  balance: string;
  currency: string;
  observed_at: string;
  projection: ProjectionSummary;
};
export type ProviderDashboardItem = {
  provider: { code: ProviderCode; display_name: string };
  balance: string;
  observed_at: string;
  feed_health: FeedHealthSummary;
  projection: ProjectionSummary;
};
export type DashboardResponse = {
  outlet: { outlet_id: string; synthetic_code: string; area: string };
  shared_cash: SharedCashDashboard;
  providers: ProviderDashboardItem[];
  alerts: unknown[];
  generated_at: string;
};

export function fetchOutlets(): Promise<OutletListItem[]> {
  return request<OutletListItem[]>("/outlets");
}
export function fetchProviders(): Promise<ProviderRef[]> {
  return request<ProviderRef[]>("/providers");
}
export function fetchDashboard(outletId: string): Promise<DashboardResponse> {
  return request<DashboardResponse>(`/outlets/${outletId}/dashboard`);
}

// --------------------------------------------------------------------------- //
// Liquidity projections (Phase 4)
// --------------------------------------------------------------------------- //
export type LiquiditySignal = {
  signal_code: string;
  label: string;
  numeric_value: string | number | null;
  unit: string | null;
  direction: string | null;
  details: Record<string, unknown> | null;
  display_order: number;
};
export type LiquidityProjection = {
  liquidity_projection_id: string | null;
  outlet_id: string;
  reserve_type: ReserveType;
  provider_id: string | null;
  as_of_at: string;
  current_balance: string;
  burn_rate_per_hour: string;
  projected_shortage_at: string | null;
  lower_bound_at: string | null;
  upper_bound_at: string | null;
  confidence_score: string;
  confidence_level: ConfidenceLevel;
  sample_count: number;
  is_actionable: boolean;
  non_actionable_reason: string | null;
  signals: LiquiditySignal[];
};
export type LiquidityProjectionListResponse = {
  outlet_id: string;
  projections: LiquidityProjection[];
  generated_at: string;
};

export function fetchLiquidityProjections(outletId: string): Promise<LiquidityProjectionListResponse> {
  return request<LiquidityProjectionListResponse>(`/outlets/${outletId}/liquidity-projections`);
}

// --------------------------------------------------------------------------- //
// Anomaly flags (Phase 4)
// --------------------------------------------------------------------------- //
export type AnomalyEvidenceItem = {
  evidence_type: string;
  label: string;
  value: unknown;
  display_order: number;
};
export type AnomalyFlag = {
  anomaly_flag_id: string | null;
  outlet_id: string;
  provider_id: string;
  window_start: string;
  window_end: string;
  pattern: string;
  confidence_score: string;
  confidence_level: ConfidenceLevel;
  disposition: AnomalyDisposition;
  reason_code: string;
  evidence_summary: string;
  plausible_benign_explanation: string;
  suppression_reason: string | null;
  evidence_items: AnomalyEvidenceItem[];
  transaction_ids: string[];
};
export type AnomalyFlagListResponse = {
  outlet_id: string;
  flags: AnomalyFlag[];
  generated_at: string;
};

export function fetchAnomalyFlags(outletId: string): Promise<AnomalyFlagListResponse> {
  return request<AnomalyFlagListResponse>(`/outlets/${outletId}/anomaly-flags`);
}
export function fetchAnomalyFlag(flagId: string): Promise<AnomalyFlag> {
  return request<AnomalyFlag>(`/anomaly-flags/${flagId}`);
}

// --------------------------------------------------------------------------- //
// Simulation + faults (Phase 3)
// --------------------------------------------------------------------------- //
export type Scenario = {
  scenario_id: string;
  code: ScenarioCode;
  name: string;
  description: string;
  default_seed: number;
  is_active: boolean;
};
export type ScenarioListResponse = { scenarios: Scenario[] };

export type FaultSummary = {
  fault_injection_id: string;
  fault_type: string;
  outlet_id: string;
  provider_id: string | null;
  parameters: Record<string, unknown>;
  is_enabled: boolean;
  scheduled_at: string;
  applied_at: string | null;
  ended_at: string | null;
};
export type RunResponse = {
  simulation_run_id: string;
  scenario_code: ScenarioCode;
  seed: number;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_summary: string | null;
  faults: FaultSummary[];
  artifacts: {
    ingestion_batches: number;
    ingestion_events: number;
    transactions: number;
    cash_snapshots: number;
    provider_snapshots: number;
  };
};

export function fetchScenarios(): Promise<ScenarioListResponse> {
  return request<ScenarioListResponse>("/simulations/scenarios");
}
export function startRun(
  scenarioCode: ScenarioCode,
  outletId: string,
  seed?: number,
): Promise<RunResponse> {
  return request<RunResponse>("/simulations/runs", {
    method: "POST",
    body: { scenario_code: scenarioCode, outlet_id: outletId, seed },
  });
}
export function fetchRun(runId: string): Promise<RunResponse> {
  return request<RunResponse>(`/simulations/runs/${runId}`);
}
export function resetRun(runId: string): Promise<RunResponse> {
  return request<RunResponse>(`/simulations/runs/${runId}/reset`, { method: "POST" });
}
export function createFault(
  runId: string,
  body: { fault_type: string; outlet_id: string; provider_id?: string | null; parameters?: Record<string, unknown> },
): Promise<FaultSummary> {
  return request<FaultSummary>(`/simulations/runs/${runId}/faults`, { method: "POST", body });
}
export function toggleFault(runId: string, faultId: string, isEnabled: boolean): Promise<FaultSummary> {
  return request<FaultSummary>(`/simulations/runs/${runId}/faults/${faultId}`, {
    method: "PATCH",
    body: { is_enabled: isEnabled },
  });
}

// --------------------------------------------------------------------------- //
// Analytics runners (Phase 4 internal controls)
// --------------------------------------------------------------------------- //
export type LiquidityRunResponse = {
  analytics_run_id: string;
  projections: LiquidityProjection[];
  candidates: { is_alertable: boolean }[];
};
export type AnomalyRunResponse = {
  analytics_run_id: string;
  flags: AnomalyFlag[];
  suppressed_count: number;
  candidates: { is_alertable: boolean }[];
};

export function runLiquidityAnalytics(simulationRunId: string, outletId: string): Promise<LiquidityRunResponse> {
  return request<LiquidityRunResponse>("/internal/analytics/liquidity/run", {
    method: "POST",
    body: { simulation_run_id: simulationRunId, outlet_id: outletId },
  });
}
export function runAnomalyAnalytics(simulationRunId: string, outletId: string): Promise<AnomalyRunResponse> {
  return request<AnomalyRunResponse>("/internal/analytics/anomalies/run", {
    method: "POST",
    body: { simulation_run_id: simulationRunId, outlet_id: outletId },
  });
}

// --------------------------------------------------------------------------- //
// Alerts (Phase 5)
// --------------------------------------------------------------------------- //
export type AlertType = "liquidity" | "anomaly" | "combined" | "data_quality";
export type Severity = "info" | "low" | "medium" | "high" | "critical";
export type AlertState = "active" | "superseded" | "closed";

export type Alert = {
  alert_id: string;
  simulation_run_id: string;
  outlet_id: string;
  provider_id: string | null;
  alert_type: AlertType;
  severity: Severity;
  state: AlertState;
  title_key: string;
  requires_case: boolean;
  detected_at: string;
  created_at: string;
  structured_payload: Record<string, unknown>;
  source_links: Record<string, unknown>;
  has_case: boolean;
  case_id: string | null;
};
export type AlertListResponse = { alerts: Alert[]; generated_at: string };

export type AlertExplanation = {
  alert_explanation_id: string;
  alert_id: string;
  locale: LocaleCode;
  situation_text: string;
  evidence_text: string;
  uncertainty_text: string;
  next_step_text: string;
  benign_context_text: string | null;
  rendered_at: string;
};
export type AlertExplanationsResponse = {
  alert_id: string;
  explanations: AlertExplanation[];
  generated_at: string;
};

export type PublishResponse = {
  published: Alert[];
  deduplicated_alert_ids: string[];
  generated_at: string;
};

export function fetchAlerts(outletId?: string): Promise<AlertListResponse> {
  const q = outletId ? `?outlet_id=${outletId}` : "";
  return request<AlertListResponse>(`/alerts${q}`);
}
export function fetchAlert(alertId: string): Promise<Alert> {
  return request<Alert>(`/alerts/${alertId}`);
}
export function fetchAlertExplanations(alertId: string): Promise<AlertExplanationsResponse> {
  return request<AlertExplanationsResponse>(`/alerts/${alertId}/explanations`);
}
export function publishAlerts(simulationRunId: string, outletId: string): Promise<PublishResponse> {
  return request<PublishResponse>("/internal/alerts/publish", {
    method: "POST",
    body: { simulation_run_id: simulationRunId, outlet_id: outletId },
  });
}

// --------------------------------------------------------------------------- //
// Cases (Phase 5)
// --------------------------------------------------------------------------- //
export type Case = {
  case_id: string;
  case_number: string;
  alert_id: string;
  outlet_id: string;
  provider_id: string | null;
  status: CaseStatus;
  current_owner_user_id: string | null;
  current_owner_role: AppRole;
  recommended_next_step: string;
  opened_at: string;
  acknowledged_at: string | null;
  escalated_at: string | null;
  resolved_at: string | null;
  resolution_summary: string | null;
  version: number;
  updated_at: string;
};
export type CaseListResponse = { cases: Case[]; generated_at: string };

export type TimelineEvent = {
  event_at: string;
  event_type: string;
  event_id: string;
  actor_user_id: string | null;
  detail: Record<string, unknown>;
};
export type CaseTimelineResponse = { case_id: string; events: TimelineEvent[]; generated_at: string };

export type AuditEvent = {
  audit_event_id: string;
  action: string;
  actor_type: string;
  actor_user_id: string | null;
  entity_type: string | null;
  occurred_at: string;
  request_id: string | null;
};
export type AuditEventsResponse = { case_id: string; events: AuditEvent[]; generated_at: string };

/** Optimistic-concurrency + idempotency envelope shared by case mutations. */
export type MutationMeta = { expected_version?: number; idempotency_key?: string; reason?: string };

export function fetchCases(status?: string): Promise<CaseListResponse> {
  const q = status ? `?status=${status}` : "";
  return request<CaseListResponse>(`/cases${q}`);
}
export function fetchCase(caseId: string): Promise<Case> {
  return request<Case>(`/cases/${caseId}`);
}
export function fetchCaseTimeline(caseId: string): Promise<CaseTimelineResponse> {
  return request<CaseTimelineResponse>(`/cases/${caseId}/timeline`);
}
export function fetchCaseAudit(caseId: string): Promise<AuditEventsResponse> {
  return request<AuditEventsResponse>(`/cases/${caseId}/audit-events`);
}
export function openCase(alertId: string, idempotencyKey?: string): Promise<Case> {
  return request<Case>(`/alerts/${alertId}/cases`, {
    method: "POST",
    body: { idempotency_key: idempotencyKey },
  });
}
export function acknowledgeCase(caseId: string, meta: MutationMeta): Promise<Case> {
  return request<Case>(`/cases/${caseId}/acknowledge`, { method: "POST", body: meta });
}
export function escalateCase(caseId: string, targetRole: AppRole | null, meta: MutationMeta): Promise<Case> {
  return request<Case>(`/cases/${caseId}/escalate`, {
    method: "POST",
    body: { ...meta, target_role: targetRole },
  });
}
export function resolveCase(caseId: string, resolutionSummary: string, meta: MutationMeta): Promise<Case> {
  return request<Case>(`/cases/${caseId}/resolve`, {
    method: "POST",
    body: { ...meta, resolution_summary: resolutionSummary },
  });
}
export function addCaseNote(
  caseId: string,
  noteText: string,
  noteType = "general",
  idempotencyKey?: string,
): Promise<unknown> {
  return request(`/cases/${caseId}/notes`, {
    method: "POST",
    body: { note_text: noteText, note_type: noteType, idempotency_key: idempotencyKey },
  });
}
export function reviewCase(
  caseId: string,
  disposition: string,
  reviewSummary: string,
  idempotencyKey?: string,
): Promise<unknown> {
  return request(`/cases/${caseId}/review`, {
    method: "POST",
    body: { disposition, review_summary: reviewSummary, idempotency_key: idempotencyKey },
  });
}

// --------------------------------------------------------------------------- //
// Notifications (Phase 5)
// --------------------------------------------------------------------------- //
export type Notification = {
  notification_id: string;
  case_id: string;
  recipient_role: AppRole;
  channel: string;
  status: "queued" | "delivered" | "read" | "failed";
  payload: Record<string, unknown>;
  queued_at: string;
  read_at: string | null;
};
export type NotificationListResponse = { notifications: Notification[]; generated_at: string };

export function fetchNotifications(): Promise<NotificationListResponse> {
  return request<NotificationListResponse>("/notifications");
}
export function markNotificationRead(notificationId: string): Promise<Notification> {
  return request<Notification>(`/notifications/${notificationId}/read`, { method: "POST" });
}
