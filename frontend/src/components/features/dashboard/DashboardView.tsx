"use client";

import Link from "next/link";
import { useDashboard } from "@/lib/queries";
import { BalanceCard } from "@/components/ui/BalanceCard";
import { LastUpdated } from "@/components/ui/LastUpdated";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Skeleton, EmptyState, ErrorState, Card, Badge } from "@/components/ui/primitives";
import { formatMoney, formatTime } from "@/lib/format";
import type { DashboardAlert, FeedHealthStatus } from "@/lib/api";

function dashboardAlertLabel(a: DashboardAlert): string {
  if (a.title_key) return a.title_key.replace(/[._]/g, " ");
  const kind = a.type ?? a.alert_type ?? "alert";
  return String(kind).replace(/_/g, " ");
}

export function DashboardView({ outletId }: { outletId: string }) {
  const { data, isLoading, error, refetch, dataUpdatedAt } = useDashboard(outletId);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-36" />
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
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium">Shared cash</h2>
        </div>
        <BalanceCard
          title="Shared cash"
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
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium">Provider balances</h2>
          <span className="text-xs text-muted">Separate — not summed</span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {data.providers.map((p) => (
            <BalanceCard
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
          <h2 className="mb-2 text-sm font-medium">Active alerts</h2>
          <div className="space-y-2">
            {data.alerts.map((a) => (
              <Card key={a.alert_id} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <Badge tone={a.severity === "high" || a.severity === "critical" ? "danger" : "warning"}>
                    {a.severity}
                  </Badge>
                  <span className="text-sm">{dashboardAlertLabel(a)}</span>
                  <span className="text-xs text-muted">{formatTime(a.detected_at)}</span>
                </div>
                <Link
                  href={a.has_case && a.case_id ? `/cases/${a.case_id}` : `/alerts/${a.alert_id}`}
                  className="text-xs text-accent hover:underline"
                >
                  {a.has_case ? "View case" : "View"}
                </Link>
              </Card>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium">Recent transactions</h2>
          <Link href={`/outlets/${outletId}/transactions`} className="text-xs text-accent hover:underline">
            View all
          </Link>
        </div>
        {data.recent_transactions && data.recent_transactions.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-subtle text-left text-xs text-muted">
                <tr>
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Provider</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_transactions.slice(0, 10).map((t) => (
                  <tr key={t.transaction_id} className="border-t border-border">
                    <td className="px-3 py-2 font-mono text-xs">{formatTime(t.occurred_at)}</td>
                    <td className="px-3 py-2 capitalize">{(t.transaction_type ?? "—").replace(/_/g, " ")}</td>
                    <td className="px-3 py-2"><ProviderChip provider={t.provider} /></td>
                    <td className="px-3 py-2 font-mono">{formatMoney(t.amount, t.currency_code)}</td>
                    <td className="px-3 py-2 capitalize">{t.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState>No recent transactions</EmptyState>
        )}
      </div>
    </div>
  );
}
