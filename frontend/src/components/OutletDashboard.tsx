"use client";

import { fetchDashboard, ProviderDashboardItem, SharedCashDashboard } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import {
  AsyncView,
  Badge,
  Card,
  ConfidenceBadge,
  FeedHealthBadge,
  formatDateTime,
  formatMoney,
  relativeToNow,
} from "@/lib/ui";

const PROVIDER_ACCENT: Record<string, string> = {
  bkash: "#e2136e",
  nagad: "#ec1c24",
  rocket: "#8c3494",
};

function ProjectionLine({
  shortageAt,
  level,
  score,
}: {
  shortageAt: string | null;
  level: string;
  score: string;
}) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
      <ConfidenceBadge level={level} score={score} />
      {shortageAt ? (
        <Badge tone="amber">Projected shortage {relativeToNow(shortageAt)}</Badge>
      ) : (
        <Badge tone="green">No shortage projected</Badge>
      )}
    </div>
  );
}

function SharedCashCard({ data }: { data: SharedCashDashboard }) {
  return (
    <Card title="Shared physical cash" subtitle="One drawer, shared across all providers" accent="#0f766e">
      <p className="text-2xl font-semibold tabular-nums">{formatMoney(data.balance, data.currency)}</p>
      <p className="mt-1 text-xs text-zinc-500">Observed {formatDateTime(data.observed_at)}</p>
      <ProjectionLine
        shortageAt={data.projection.shortage_at}
        level={data.projection.confidence_level}
        score={data.projection.confidence_score}
      />
    </Card>
  );
}

function ProviderCard({ item }: { item: ProviderDashboardItem }) {
  const code = item.provider.code;
  return (
    <Card
      title={`${item.provider.display_name} e-money`}
      subtitle="Provider reserve — tracked separately"
      accent={PROVIDER_ACCENT[code]}
    >
      <p className="text-2xl font-semibold tabular-nums">{formatMoney(item.balance)}</p>
      <p className="mt-1 text-xs text-zinc-500">Observed {formatDateTime(item.observed_at)}</p>
      <div className="mt-2">
        <FeedHealthBadge status={item.feed_health.status} />
      </div>
      <ProjectionLine
        shortageAt={item.projection.shortage_at}
        level={item.projection.confidence_level}
        score={item.projection.confidence_score}
      />
    </Card>
  );
}

export default function OutletDashboard({ outletId, refreshKey }: { outletId: string; refreshKey: number }) {
  // Poll every 4s during the demo (Phase 6: 3–5s dashboard refresh).
  const { state, reload } = useAsync(() => fetchDashboard(outletId), [outletId, refreshKey], 4000);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Outlet dashboard</h2>
          <p className="text-xs text-zinc-500">
            Reserves are shown separately and are never summed into a blended total.
          </p>
        </div>
        <Badge tone="blue">Auto-refresh · 4s</Badge>
      </div>

      <AsyncView state={state} onRetry={reload}>
        {(d) => (
          <>
            <p className="text-xs text-zinc-500">
              {d.outlet.synthetic_code} · {d.outlet.area} · generated {formatDateTime(d.generated_at)}
            </p>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <SharedCashCard data={d.shared_cash} />
              {d.providers.map((p) => (
                <ProviderCard key={p.provider.code} item={p} />
              ))}
            </div>
            <p className="text-xs text-zinc-400">
              Decision-support view only. Figures are synthetic and for review, not settlement.
            </p>
          </>
        )}
      </AsyncView>
    </div>
  );
}
