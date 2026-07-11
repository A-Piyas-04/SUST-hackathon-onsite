import { useQuery } from "@tanstack/react-query";
import {
  fetchAlerts,
  fetchAnomalyFlag,
  fetchAnomalyFlags,
  fetchCase,
  fetchCaseAudit,
  fetchCaseTimeline,
  fetchCases,
  fetchDashboard,
  fetchDataQuality,
  fetchDataQualityHistory,
  fetchAlert,
  fetchAlertExplanations,
  fetchLiquidityProjections,
  fetchMetrics,
  fetchNotifications,
  fetchOutlets,
  fetchRun,
  fetchScenarios,
  fetchTransactions,
  fetchValidationResults,
  type ProviderCode,
  type TransactionType,
} from "@/lib/api";

export const queryKeys = {
  dashboard: (outletId: string) => ["dashboard", outletId] as const,
  outlets: ["outlets"] as const,
  liquidity: (outletId: string) => ["liquidity", outletId] as const,
  anomalies: (outletId: string) => ["anomalies", outletId] as const,
  anomaly: (id: string) => ["anomaly", id] as const,
  alerts: (outletId?: string) => ["alerts", outletId] as const,
  alert: (id: string) => ["alert", id] as const,
  alertExplanations: (id: string) => ["alert-explanations", id] as const,
  cases: (status?: string) => ["cases", status] as const,
  case: (id: string) => ["case", id] as const,
  caseTimeline: (id: string) => ["case-timeline", id] as const,
  caseAudit: (id: string) => ["case-audit", id] as const,
  notifications: ["notifications"] as const,
  transactions: (outletId: string, params: object) => ["transactions", outletId, params] as const,
  dataQuality: (outletId: string) => ["data-quality", outletId] as const,
  dataQualityHistory: (outletId: string) => ["data-quality-history", outletId] as const,
  scenarios: ["scenarios"] as const,
  run: (id: string) => ["run", id] as const,
  validation: ["validation"] as const,
  metrics: ["metrics"] as const,
};

export function useDashboard(outletId: string) {
  return useQuery({
    queryKey: queryKeys.dashboard(outletId),
    queryFn: () => fetchDashboard(outletId),
    enabled: !!outletId,
    refetchInterval: 30_000,
  });
}

export function useOutlets() {
  return useQuery({ queryKey: queryKeys.outlets, queryFn: fetchOutlets });
}

export function useLiquidity(outletId: string) {
  return useQuery({
    queryKey: queryKeys.liquidity(outletId),
    queryFn: () => fetchLiquidityProjections(outletId),
    enabled: !!outletId,
    refetchInterval: 30_000,
  });
}

export function useAnomalies(outletId: string) {
  return useQuery({
    queryKey: queryKeys.anomalies(outletId),
    queryFn: () => fetchAnomalyFlags(outletId),
    enabled: !!outletId,
  });
}

export function useAnomaly(flagId: string) {
  return useQuery({
    queryKey: queryKeys.anomaly(flagId),
    queryFn: () => fetchAnomalyFlag(flagId),
    enabled: !!flagId,
  });
}

export function useAlerts(outletId?: string) {
  return useQuery({
    queryKey: queryKeys.alerts(outletId),
    queryFn: () => fetchAlerts(outletId),
    refetchInterval: 30_000,
  });
}

export function useAlert(alertId: string) {
  return useQuery({
    queryKey: queryKeys.alert(alertId),
    queryFn: () => fetchAlert(alertId),
    enabled: !!alertId,
  });
}

export function useAlertExplanations(alertId: string) {
  return useQuery({
    queryKey: queryKeys.alertExplanations(alertId),
    queryFn: () => fetchAlertExplanations(alertId),
    enabled: !!alertId,
  });
}

export function useCases(status?: string) {
  return useQuery({
    queryKey: queryKeys.cases(status),
    queryFn: () => fetchCases(status),
    refetchOnWindowFocus: true,
  });
}

export function useCase(caseId: string) {
  return useQuery({
    queryKey: queryKeys.case(caseId),
    queryFn: () => fetchCase(caseId),
    enabled: !!caseId,
    refetchOnWindowFocus: true,
  });
}

export function useCaseTimeline(caseId: string) {
  return useQuery({
    queryKey: queryKeys.caseTimeline(caseId),
    queryFn: () => fetchCaseTimeline(caseId),
    enabled: !!caseId,
  });
}

export function useCaseAudit(caseId: string) {
  return useQuery({
    queryKey: queryKeys.caseAudit(caseId),
    queryFn: () => fetchCaseAudit(caseId),
    enabled: !!caseId,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: fetchNotifications,
    refetchInterval: 15_000,
  });
}

export function useTransactions(
  outletId: string,
  params: { provider_code?: ProviderCode; transaction_type?: TransactionType; page?: number; page_size?: number },
) {
  return useQuery({
    queryKey: queryKeys.transactions(outletId, params),
    queryFn: () => fetchTransactions(outletId, params),
    enabled: !!outletId,
  });
}

export function useDataQuality(outletId: string) {
  return useQuery({
    queryKey: queryKeys.dataQuality(outletId),
    queryFn: () => fetchDataQuality(outletId),
    enabled: !!outletId,
    refetchInterval: 30_000,
  });
}

export function useDataQualityHistory(outletId: string) {
  return useQuery({
    queryKey: queryKeys.dataQualityHistory(outletId),
    queryFn: () => fetchDataQualityHistory(outletId),
    enabled: !!outletId,
  });
}

export function useScenarios() {
  return useQuery({ queryKey: queryKeys.scenarios, queryFn: fetchScenarios });
}

export function useRun(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.run(runId ?? ""),
    queryFn: () => fetchRun(runId!),
    enabled: !!runId,
    refetchInterval: (q) => (q.state.data?.status === "running" ? 5_000 : false),
  });
}

export function useValidation() {
  return useQuery({ queryKey: queryKeys.validation, queryFn: () => fetchValidationResults() });
}

export function useMetrics() {
  return useQuery({ queryKey: queryKeys.metrics, queryFn: fetchMetrics });
}
