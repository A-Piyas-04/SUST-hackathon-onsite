"use client";

import { AnomalyEvidenceItem, AnomalyFlag, fetchAnomalyFlags } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { AsyncView, Badge, Card, ConfidenceBadge, DispositionBadge, EmptyState, formatDateTime } from "@/lib/ui";

function renderEvidenceValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${v}`)
      .join(" · ");
  }
  return String(value);
}

function EvidenceTable({ items }: { items: AnomalyEvidenceItem[] }) {
  return (
    <table className="w-full text-xs">
      <tbody>
        {items
          .slice()
          .sort((a, b) => a.display_order - b.display_order)
          .map((e) => (
            <tr key={e.evidence_type} className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
              <td className="py-1 pr-2 align-top font-medium text-zinc-500">{e.label}</td>
              <td className="py-1 tabular-nums">{renderEvidenceValue(e.value)}</td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}

function FlagCard({ f }: { f: AnomalyFlag }) {
  const suppressed = f.disposition === "suppressed_data_quality";
  return (
    <Card
      title={f.pattern.replace(/_/g, " ")}
      subtitle={`Window ${formatDateTime(f.window_start)} → ${formatDateTime(f.window_end)}`}
      right={<DispositionBadge disposition={f.disposition} />}
      accent={suppressed ? "#94a3b8" : "#d97706"}
    >
      <div className="flex flex-wrap items-center gap-2">
        <ConfidenceBadge level={f.confidence_level} score={f.confidence_score} />
        <Badge tone="zinc">{f.transaction_ids.length} transactions</Badge>
        {suppressed && <Badge tone="slate">Measurement only — not an actionable alert</Badge>}
      </div>

      <p className="mt-3 text-sm">{f.evidence_summary}</p>

      <div className="mt-3 rounded-lg border border-zinc-200 p-2 dark:border-zinc-800">
        <p className="mb-1 text-xs font-medium text-zinc-500">Structured evidence</p>
        <EvidenceTable items={f.evidence_items} />
      </div>

      {/* Benign context is displayed prominently, per guardrail 6. */}
      <div className="mt-3 rounded-lg bg-emerald-50 p-2 text-xs text-emerald-900 dark:bg-emerald-900/20 dark:text-emerald-200">
        <p className="font-medium">Plausible benign context</p>
        <p className="mt-0.5">{f.plausible_benign_explanation}</p>
      </div>

      {suppressed && f.suppression_reason && (
        <p className="mt-2 rounded bg-zinc-100 p-2 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          <span className="font-medium">Suppressed:</span> {f.suppression_reason}
        </p>
      )}
    </Card>
  );
}

export default function AnomalyPanel({ outletId, refreshKey }: { outletId: string; refreshKey: number }) {
  const { state, reload } = useAsync(() => fetchAnomalyFlags(outletId), [outletId, refreshKey]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Anomaly evidence</h2>
        <p className="text-xs text-zinc-500">
          Unusual-pattern summaries with structured evidence and benign context. Suppressed evaluations are visible for
          measurement but clearly marked as non-alertable.
        </p>
      </div>
      <AsyncView
        state={state}
        onRetry={reload}
        isEmpty={(d) => d.flags.length === 0}
        empty={
          <EmptyState>
            No anomaly evaluations yet. Run a scenario (B or C) and trigger anomaly analytics in{" "}
            <strong>Scenarios &amp; Faults</strong>.
          </EmptyState>
        }
      >
        {(d) => {
          const review = d.flags.filter((f) => f.disposition !== "suppressed_data_quality");
          const suppressed = d.flags.filter((f) => f.disposition === "suppressed_data_quality");
          return (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {review.map((f, i) => (
                  <FlagCard key={f.anomaly_flag_id ?? `r${i}`} f={f} />
                ))}
              </div>
              {suppressed.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
                    Suppressed (degraded data) — not alertable
                  </p>
                  <div className="grid gap-4 md:grid-cols-2">
                    {suppressed.map((f, i) => (
                      <FlagCard key={f.anomaly_flag_id ?? `s${i}`} f={f} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        }}
      </AsyncView>
    </div>
  );
}
