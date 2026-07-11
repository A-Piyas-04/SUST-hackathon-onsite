"use client";

import { useState } from "react";
import { useDataQuality, useDataQualityHistory } from "@/lib/queries";
import { FeedStatusBadge } from "@/components/ui/FeedStatusDot";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime, parseEventStats, providerDisplayName, PROVIDER_COLORS, confidencePct } from "@/lib/format";
import type { FeedHealthStatus, ProviderCode } from "@/lib/api";

const STATUS_DOT: Record<FeedHealthStatus, string> = {
  fresh: "bg-success",
  stale: "bg-warning",
  missing: "bg-danger",
  conflicting: "bg-danger",
};

function confidenceFromModifier(modifier: number): string {
  return `${confidencePct(modifier)}%`;
}

export function DataQualityView({ outletId }: { outletId: string }) {
  const { data, isLoading, error, refetch } = useDataQuality(outletId);
  const { data: history } = useDataQualityHistory(outletId);
  const [showAllHistory, setShowAllHistory] = useState(false);

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!data) return <EmptyState>No data</EmptyState>;

  const historyRows = history?.assessments ?? [];
  const visibleHistory = showAllHistory ? historyRows : historyRows.slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-3">
        {data.providers.map((p) => {
          const stats = parseEventStats(p.assessment.summary);
          const stripe = PROVIDER_COLORS[p.provider];
          return (
            <Card key={p.provider} topStripe={stripe} className="px-5 py-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-foreground">
                  {providerDisplayName(p.provider)}
                </p>
                <FeedStatusBadge status={p.assessment.status as FeedHealthStatus} />
              </div>
              <p className="mt-2 font-mono text-xs text-muted">
                {p.assessment.latest_source_at ? formatTime(p.assessment.latest_source_at) : "—"}
              </p>
              <p className="mt-2 text-[13px] text-secondary">
                Confidence: {confidenceFromModifier(p.assessment.confidence_modifier)}
              </p>
              <p className="mt-2 text-xs text-muted">
                {stats
                  ? `Events accepted: ${stats.accepted} · Rejected: ${stats.rejected}`
                  : "Events accepted: — · Rejected: —"}
              </p>
            </Card>
          );
        })}
      </div>

      {historyRows.length > 0 && (
        <div>
          <h2 className="section-heading mb-3">History</h2>
          <div className="overflow-hidden rounded-[12px] border border-border">
            {visibleHistory.map((a, idx) => (
              <div
                key={`${a.provider}-${a.assessment.assessed_at}-${idx}`}
                className="flex items-center gap-3 border-b border-border bg-surface px-4 py-2.5 last:border-b-0"
              >
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[a.assessment.status as FeedHealthStatus] ?? "bg-muted"}`}
                />
                <span className="w-14 shrink-0 font-mono text-xs text-muted">
                  {formatTime(a.assessment.assessed_at)}
                </span>
                <ProviderChip provider={a.provider as ProviderCode} />
                <span className="ml-auto">
                  <FeedStatusBadge status={a.assessment.status as FeedHealthStatus} />
                </span>
              </div>
            ))}
          </div>
          {historyRows.length > 10 && (
            <button
              type="button"
              className="link-maroon mt-2"
              onClick={() => setShowAllHistory((v) => !v)}
            >
              {showAllHistory ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
