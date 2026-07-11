"use client";

import Link from "next/link";
import { useAnomalies, useAnomaly } from "@/lib/queries";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Badge, Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";
import { ApiError } from "@/lib/api";

export function AnomaliesListView({ outletId }: { outletId: string }) {
  const { data, isLoading, error, refetch } = useAnomalies(outletId);

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!data?.flags.length) return <EmptyState>No flags</EmptyState>;

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted">Advisory only — no account action.</p>
      {data.flags.map((f) => (
        <Card key={f.anomaly_flag_id ?? f.pattern}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Badge tone="danger">high</Badge>
                <span className="text-sm capitalize">{f.pattern.replace(/_/g, " ")}</span>
                <span className="text-xs text-muted">{formatTime(f.window_end)}</span>
              </div>
              <p className="mt-1 text-sm text-secondary">{f.evidence_summary}</p>
              <div className="mt-2"><ConfidenceBar score={f.confidence_score} level={f.confidence_level} /></div>
            </div>
            {f.anomaly_flag_id && (
              <Link href={`/outlets/${outletId}/anomalies/${f.anomaly_flag_id}`} className="text-xs text-accent hover:underline">
                Evidence
              </Link>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}

export function AnomalyDetailView({ outletId, flagId }: { outletId: string; flagId: string }) {
  const { data: f, isLoading, error, refetch } = useAnomaly(flagId);

  if (isLoading) return <Skeleton className="h-64" />;
  if (error instanceof ApiError && error.kind === "notFound") return <EmptyState>Not found</EmptyState>;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!f) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link href={`/outlets/${outletId}/anomalies`} className="text-xs text-accent hover:underline">← Anomalies</Link>
      <h2 className="text-lg font-semibold capitalize">{f.pattern.replace(/_/g, " ")}</h2>
      <ConfidenceBar score={f.confidence_score} level={f.confidence_level} />

      <Card>
        <p className="text-xs font-medium text-muted">Detected</p>
        <p className="text-sm">{f.evidence_summary}</p>
      </Card>

      {f.plausible_benign_explanation && (
        <Card className="border-success/30 bg-success/5">
          <p className="text-xs font-medium text-success">Benign context</p>
          <p className="text-sm">{f.plausible_benign_explanation}</p>
        </Card>
      )}

      {f.evidence_items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-subtle text-left text-xs text-muted">
              <tr>
                <th className="px-3 py-2">Evidence</th>
                <th className="px-3 py-2">Value</th>
              </tr>
            </thead>
            <tbody>
              {f.evidence_items.map((e) => (
                <tr key={e.label} className="border-t border-border">
                  <td className="px-3 py-2">{e.label}</td>
                  <td className="px-3 py-2 font-mono text-xs">{String(e.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
