"use client";

import { useDataQuality, useDataQualityHistory } from "@/lib/queries";
import { FeedStatusDot } from "@/components/ui/FeedStatusDot";
import { Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";
import type { FeedHealthStatus } from "@/lib/api";

export function DataQualityView({ outletId }: { outletId: string }) {
  const { data, isLoading, error, refetch } = useDataQuality(outletId);
  const { data: history } = useDataQualityHistory(outletId);

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!data) return <EmptyState>No data</EmptyState>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        {data.providers.map((p) => (
          <Card key={p.provider}>
            <p className="text-sm font-medium capitalize">{p.provider}</p>
            <div className="mt-2">
              <FeedStatusDot status={p.assessment.status as FeedHealthStatus} />
            </div>
            <p className="mt-2 text-xs text-muted">
              {p.assessment.latest_source_at ? formatTime(p.assessment.latest_source_at) : "—"}
            </p>
            <p className="mt-1 text-xs text-muted">Modifier {p.assessment.confidence_modifier}</p>
          </Card>
        ))}
      </div>

      <div>
        <p className="mb-2 text-sm font-medium">Impact</p>
        <ul className="space-y-1 text-sm text-secondary">
          {data.providers.map((p) => (
            <li key={p.provider}>
              • <span className="capitalize">{p.provider}</span>: {p.assessment.summary || p.assessment.status}
            </li>
          ))}
        </ul>
      </div>

      {history?.assessments && history.assessments.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium">History</p>
          <div className="space-y-1">
            {history.assessments.slice(0, 10).map((a, idx) => (
              <p key={idx} className="text-xs text-muted">
                {formatTime(a.assessment.assessed_at)} — <span className="capitalize">{a.provider}</span>: {a.assessment.status}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
