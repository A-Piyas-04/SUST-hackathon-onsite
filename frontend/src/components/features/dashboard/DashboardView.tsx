"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDashboard } from "@/lib/queries";
import { SharedCashCard, ProviderBalanceCard } from "@/components/ui/BalanceCard";
import { LastUpdated } from "@/components/ui/LastUpdated";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Skeleton, ErrorState, Badge, Button } from "@/components/ui/primitives";
import { formatMoney, formatTime, providerDisplayName } from "@/lib/format";
import type { DashboardAlert, FeedHealthStatus, ProviderCode } from "@/lib/api";

function dashboardAlertLabel(a: DashboardAlert): string {
  if (a.title_key) return a.title_key.replace(/[._]/g, " ");
  const kind = a.type ?? a.alert_type ?? "alert";
  return String(kind).replace(/_/g, " ");
}

function alertSeverityTone(severity: string): "danger" | "warning" | "info" {
  if (severity === "high" || severity === "critical") return "danger";
  if (severity === "medium") return "warning";
  return "info";
}

function alertProviderCode(a: DashboardAlert): ProviderCode | null {
  const raw = (a as { provider?: string }).provider ?? a.provider_id ?? "";
  const lower = String(raw).toLowerCase();
  if (lower.includes("bkash")) return "bkash";
  if (lower.includes("nagad")) return "nagad";
  if (lower.includes("rocket")) return "rocket";
  return null;
}

export function DashboardView({ outletId }: { outletId: string }) {
  const router = useRouter();
  const { data, isLoading, error, refetch, dataUpdatedAt } = useDashboard(outletId);

  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-40" />
        ))}
      </div>
    );
  }

  if (error) return <ErrorState message="Could not load data" onRetry={() => refetch()} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-secondary">
          {data.outlet.synthetic_code} · {data.outlet.area}
        </p>
        <LastUpdated generatedAt={new Date(dataUpdatedAt).toISOString()} onRefresh={() => refetch()} />
      </div>

      <div>
        <h2 className="section-heading mb-3">Shared cash</h2>
        <SharedCashCard
          balance={data.shared_cash.balance}
          currency={data.shared_cash.currency}
          observedAt={data.shared_cash.observed_at}
          shortageAt={data.shared_cash.projection.shortage_at}
          confidenceScore={data.shared_cash.projection.confidence_score}
          confidenceLevel={data.shared_cash.projection.confidence_level}
          projectionHref={`/outlets/${outletId}/liquidity`}
        />
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="section-heading">Provider balances</h2>
          <span className="text-xs text-muted">Separate — not summed</span>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {data.providers.map((p) => (
            <ProviderBalanceCard
              key={p.provider.code}
              title={p.provider.display_name}
              balance={p.balance}
              observedAt={p.observed_at}
              feedStatus={p.feed_health.status as FeedHealthStatus}
              shortageAt={p.projection.shortage_at}
              confidenceScore={p.projection.confidence_score}
              confidenceLevel={p.projection.confidence_level}
              provider={p.provider.code}
              projectionHref={`/outlets/${outletId}/liquidity`}
              missing={p.feed_health.status === "missing"}
            />
          ))}
        </div>
      </div>

      {Array.isArray(data.alerts) && data.alerts.length > 0 && (
        <div>
          <h2 className="section-heading mb-3">Active alerts</h2>
          <div className="overflow-hidden rounded-[12px] border border-border">
            {data.alerts.map((a) => {
              const label = dashboardAlertLabel(a);
              const provider = alertProviderCode(a);
              return (
                <div
                  key={a.alert_id}
                  className="flex flex-col gap-3 border-b border-border bg-surface px-4 py-3 last:border-b-0 hover:bg-surface-raised sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
                    <Badge tone={alertSeverityTone(String(a.severity))}>{a.severity}</Badge>
                    <span className="text-sm font-medium capitalize text-foreground">{label}</span>
                    {provider && <ProviderChip provider={provider} />}
                    <span className="font-mono text-xs text-muted">{formatTime(a.detected_at)}</span>
                    <span className="w-full text-xs text-muted sm:w-auto">
                      {label.slice(0, 80)}
                      {a.type ? ` · ${String(a.type).replace(/_/g, " ")}` : ""}
                    </span>
                  </div>
                  <Link href={a.has_case && a.case_id ? `/cases/${a.case_id}` : `/alerts/${a.alert_id}`}>
                    <Button size="sm" variant="outline">
                      View →
                    </Button>
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="section-heading">Recent transactions</h2>
          <Link href={`/outlets/${outletId}/transactions`} className="link-maroon">
            View all →
          </Link>
        </div>
        {data.recent_transactions && data.recent_transactions.length > 0 ? (
          <div className="overflow-x-auto rounded-[12px] border border-border">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Provider</th>
                  <th className="text-right">Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_transactions.slice(0, 10).map((t) => (
                  <tr key={t.transaction_id}>
                    <td className="font-mono text-xs text-muted">{formatTime(t.occurred_at)}</td>
                    <td className="capitalize">{(t.transaction_type ?? "—").replace(/_/g, " ")}</td>
                    <td>
                      <ProviderChip provider={t.provider} />
                    </td>
                    <td className="text-right font-mono">{formatMoney(t.amount, t.currency_code)}</td>
                    <td className="capitalize">{t.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-[13px] text-[var(--text-faint)]">
            No transactions recorded yet — run a scenario to generate data.{" "}
            <button type="button" className="link-maroon" onClick={() => router.push("/scenarios")}>
              → Go to Scenarios
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
