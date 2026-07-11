"use client";

import { fetchLiquidityProjections, LiquidityProjection, Principal } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import {
  AsyncView,
  Badge,
  Card,
  ConfidenceBadge,
  EmptyState,
  formatDateTime,
  formatMoney,
  relativeToNow,
} from "@/lib/ui";

function reserveLabel(p: LiquidityProjection): string {
  if (p.reserve_type === "shared_cash") return "Shared physical cash";
  return "Provider e-money reserve";
}

function directionTone(direction: string | null): "red" | "green" | "slate" {
  if (direction === "increases_pressure") return "red";
  if (direction === "reduces_pressure") return "green";
  return "slate";
}

function ProjectionCard({ p }: { p: LiquidityProjection }) {
  const degraded = !p.is_actionable || p.confidence_level === "low" || p.confidence_level === "unavailable";
  const hasShortage = !!p.projected_shortage_at;
  return (
    <Card
      title={reserveLabel(p)}
      subtitle={p.reserve_type === "provider_e_money" ? `Account ${p.provider_id?.slice(0, 8)}…` : "Outlet-wide"}
    >
      <div className="flex flex-wrap items-center gap-2">
        <ConfidenceBadge level={p.confidence_level} score={p.confidence_score} />
        {degraded ? (
          <Badge tone="slate">Not a confident shortage signal</Badge>
        ) : hasShortage ? (
          <Badge tone="amber">Shortage {relativeToNow(p.projected_shortage_at)}</Badge>
        ) : (
          <Badge tone="green">Stable / no shortage</Badge>
        )}
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-xs text-zinc-500">Current balance</dt>
          <dd className="tabular-nums">{formatMoney(p.current_balance)}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Burn rate / hour</dt>
          <dd className="tabular-nums">{formatMoney(p.burn_rate_per_hour)}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Est. shortage time</dt>
          <dd>{hasShortage ? formatDateTime(p.projected_shortage_at) : "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-zinc-500">Uncertainty window</dt>
          <dd className="text-xs">
            {p.lower_bound_at ? `${formatDateTime(p.lower_bound_at)} → ${formatDateTime(p.upper_bound_at)}` : "—"}
          </dd>
        </div>
      </dl>

      {p.non_actionable_reason && (
        <p className="mt-2 rounded bg-zinc-100 p-2 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {p.non_actionable_reason}
        </p>
      )}

      <div className="mt-3">
        <p className="mb-1 text-xs font-medium text-zinc-500">Contributing signals</p>
        <ul className="space-y-1">
          {p.signals
            .slice()
            .sort((a, b) => a.display_order - b.display_order)
            .map((s) => (
              <li key={s.signal_code} className="flex items-center justify-between gap-2 text-xs">
                <span>{s.label}</span>
                <span className="flex items-center gap-1.5 tabular-nums">
                  {s.numeric_value !== null && (
                    <span className="text-zinc-600 dark:text-zinc-300">
                      {s.numeric_value} {s.unit ?? ""}
                    </span>
                  )}
                  {s.direction && <Badge tone={directionTone(s.direction)}>{s.direction.replace(/_/g, " ")}</Badge>}
                </span>
              </li>
            ))}
        </ul>
      </div>
    </Card>
  );
}

export default function LiquidityPanel({
  outletId,
  refreshKey,
  user: _user,
}: {
  outletId: string;
  refreshKey: number;
  user: Principal;
}) {
  const { state, reload } = useAsync(() => fetchLiquidityProjections(outletId), [outletId, refreshKey]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Liquidity intelligence</h2>
        <p className="text-xs text-zinc-500">
          Shortage timing and confidence per reserve. Degraded or low-confidence projections are shown, but never as a
          confident shortage.
        </p>
      </div>
      <AsyncView
        state={state}
        onRetry={reload}
        isEmpty={(d) => d.projections.length === 0}
        empty={
          <EmptyState>
            No liquidity projections yet. Start a scenario run and trigger liquidity analytics in{" "}
            <strong>Scenarios &amp; Faults</strong>.
          </EmptyState>
        }
      >
        {(d) => (
          <div className="grid gap-4 md:grid-cols-2">
            {d.projections
              .slice()
              .sort((a) => (a.reserve_type === "shared_cash" ? -1 : 1))
              .map((p, i) => (
                <ProjectionCard key={p.liquidity_projection_id ?? i} p={p} />
              ))}
          </div>
        )}
      </AsyncView>
    </div>
  );
}
