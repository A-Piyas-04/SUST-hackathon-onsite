"use client";

import { useValidation, useMetrics } from "@/lib/queries";
import { Card, ErrorState, Skeleton } from "@/components/ui/primitives";

export function MetricsView() {
  const validation = useValidation();
  const metrics = useMetrics();

  if (validation.isLoading || metrics.isLoading) return <Skeleton className="h-48" />;
  if (validation.error && metrics.error) return <ErrorState message="Could not load" />;

  const latest = validation.data?.runs[0];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        {latest?.metrics.slice(0, 3).map((m) => (
          <Card key={m.metric_code}>
            <p className="text-xs text-muted capitalize">{m.metric_code.replace(/_/g, " ")}</p>
            <p className="font-mono text-2xl font-semibold">{m.value}{m.unit === "percent" ? "%" : ""}</p>
            <p className="text-xs text-muted">n={m.sample_size}</p>
          </Card>
        ))}
      </div>

      {metrics.data?.process && (
        <Card>
          <p className="mb-2 text-sm font-medium">Performance</p>
          <pre className="overflow-x-auto text-xs text-secondary">{JSON.stringify(metrics.data.process, null, 2)}</pre>
        </Card>
      )}

      <Card>
        <p className="text-xs text-muted">Held-out synthetic data · single rule · not production-validated</p>
      </Card>
    </div>
  );
}
