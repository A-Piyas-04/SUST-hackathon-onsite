"use client";

import { useState } from "react";
import { useLiquidity } from "@/lib/queries";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { FeedStatusDot } from "@/components/ui/FeedStatusDot";
import { Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatMoney, relativeToNow } from "@/lib/format";
import type { LiquidityProjection, ReserveType } from "@/lib/api";
import { ConfidenceConeChart } from "@/components/ui/ConfidenceConeChart";

const TABS: { key: ReserveType | "shared"; label: string }[] = [
  { key: "shared_cash", label: "Shared" },
  { key: "provider_e_money", label: "bKash" },
  { key: "provider_e_money", label: "Nagad" },
  { key: "provider_e_money", label: "Rocket" },
];

export function LiquidityView({ outletId }: { outletId: string }) {
  const { data, isLoading, error, refetch } = useLiquidity(outletId);
  const [tab, setTab] = useState(0);

  if (isLoading) return <Skeleton className="h-64" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!data?.projections.length) return <EmptyState>No projections</EmptyState>;

  const projections = data.projections;
  const shared = projections.find((p) => p.reserve_type === "shared_cash");
  const providers = ["bkash", "nagad", "rocket"].map((code) =>
    projections.find((p) => p.reserve_type === "provider_e_money" && (p as LiquidityProjection & { provider_code?: string }).provider_code === code) ??
    projections.filter((p) => p.reserve_type === "provider_e_money")[["bkash", "nagad", "rocket"].indexOf(code)],
  );
  const selected = tab === 0 ? shared : providers[tab - 1];

  return (
    <div className="space-y-4">
      <div className="flex gap-1 rounded-md border border-border p-0.5">
        {["Shared", "bKash", "Nagad", "Rocket"].map((label, i) => (
          <button
            key={label}
            type="button"
            onClick={() => setTab(i)}
            className={`rounded px-3 py-1 text-xs ${tab === i ? "bg-accent text-white" : "text-secondary hover:bg-subtle"}`}
          >
            {label}
          </button>
        ))}
      </div>

      {selected && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <p className="text-xs text-muted">Balance</p>
              <p className="font-mono text-xl font-semibold">{formatMoney(selected.current_balance)}</p>
              <p className="mt-2 text-xs text-muted">Burn ~{selected.burn_rate_per_hour}/hr</p>
            </Card>
            <Card>
              <p className="text-xs text-muted">Projection</p>
              {selected.projected_shortage_at ? (
                <p className="text-sm text-warning">Shortage {relativeToNow(selected.projected_shortage_at)}</p>
              ) : (
                <p className="text-sm text-success">No shortage</p>
              )}
              <div className="mt-2">
                <ConfidenceBar score={selected.confidence_score} level={selected.confidence_level} />
              </div>
            </Card>
          </div>

          {selected.signals.length > 0 && (
            <Card>
              <p className="mb-2 text-sm font-medium">Signals</p>
              <ul className="space-y-1 text-sm text-secondary">
                {selected.signals.map((s) => (
                  <li key={s.signal_code}>• {s.label}</li>
                ))}
              </ul>
            </Card>
          )}

          <ConfidenceConeChart
            balance={Number(selected.current_balance)}
            shortageAt={selected.projected_shortage_at}
            confidence={Number(selected.confidence_score)}
            lowerBound={selected.lower_bound_at}
            upperBound={selected.upper_bound_at}
          />
        </>
      )}
    </div>
  );
}
