"use client";

import {
  fetchValidationResults,
  MetricResultDetail,
  ValidationMetricPayload,
} from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { AsyncView, Badge, BadgeTone, Card, EmptyState, formatDateTime } from "@/lib/ui";

const CATEGORY_TONE: Record<string, BadgeTone> = {
  analytics: "violet",
  performance: "blue",
  reliability: "green",
  explainability: "amber",
};

function MetricCard({ m }: { m: MetricResultDetail }) {
  return (
    <Card
      title={m.metric_code}
      subtitle={`${m.category} · n=${m.sample_size}`}
      right={<Badge tone={CATEGORY_TONE[m.category] ?? "zinc"}>{m.category}</Badge>}
    >
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums">{m.value}</span>
        <span className="text-xs text-zinc-500">{m.unit}</span>
      </div>
      <dl className="mt-3 space-y-2 text-xs">
        <div>
          <dt className="font-medium text-zinc-500">Method</dt>
          <dd className="text-zinc-700 dark:text-zinc-300">{m.method}</dd>
        </div>
        <div>
          <dt className="font-medium text-zinc-500">Limitations</dt>
          <dd className="text-zinc-700 dark:text-zinc-300">{m.limitations}</dd>
        </div>
        <div>
          <dt className="font-medium text-zinc-500">Computed</dt>
          <dd className="text-zinc-600">{formatDateTime(m.computed_at)}</dd>
        </div>
      </dl>
    </Card>
  );
}

function RunMeta({ run }: { run: ValidationMetricPayload }) {
  const rc = (run.configuration?.release_candidate ?? {}) as {
    commit?: string;
    contract_version?: string;
  };
  return (
    <Card
      title={run.name}
      subtitle="Latest completed held-out validation run"
      right={<Badge tone={run.status === "completed" ? "green" : "amber"}>{run.status}</Badge>}
    >
      <dl className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
        <div>
          <dt className="text-zinc-500">Dataset split</dt>
          <dd className="font-medium">{run.dataset_split}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Engine version</dt>
          <dd className="font-medium">{run.engine_version}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Metrics</dt>
          <dd className="font-medium">{run.metrics.length}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Started</dt>
          <dd>{formatDateTime(run.started_at)}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Completed</dt>
          <dd>{formatDateTime(run.completed_at)}</dd>
        </div>
        {rc.commit && (
          <div>
            <dt className="text-zinc-500">Release commit</dt>
            <dd className="font-mono">{rc.commit.slice(0, 10)}</dd>
          </div>
        )}
      </dl>
    </Card>
  );
}

export default function ValidationPanel({ refreshKey }: { refreshKey: number }) {
  const { state, reload } = useAsync(
    () => fetchValidationResults({ status: "completed", datasetSplit: "held_out" }),
    [refreshKey],
  );

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Validation evidence</h2>
        <p className="text-xs text-zinc-500">
          Honest measured metrics from the frozen held-out evaluation. Values reflect a small synthetic
          sample — read each card&apos;s method and limitations. Management/admin only.
        </p>
      </div>
      <AsyncView
        state={state}
        onRetry={reload}
        isEmpty={(d) => d.runs.length === 0 || d.runs[0].metrics.length === 0}
        empty={
          <EmptyState>
            No completed held-out validation run yet. Run <code>make validate</code> in the backend to
            generate evidence.
          </EmptyState>
        }
      >
        {(d) => {
          const run = d.runs[0];
          return (
            <div className="space-y-4">
              <RunMeta run={run} />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {run.metrics.map((m) => (
                  <MetricCard key={m.metric_code} m={m} />
                ))}
              </div>
            </div>
          );
        }}
      </AsyncView>
    </div>
  );
}
