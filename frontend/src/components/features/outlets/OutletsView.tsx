"use client";

import Link from "next/link";
import { useOutlets, useDashboard } from "@/lib/queries";
import { Badge, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatMoney } from "@/lib/format";
import { FeedStatusDot } from "@/components/ui/FeedStatusDot";
import type { FeedHealthStatus } from "@/lib/api";

function OutletRow({ outletId, code, name }: { outletId: string; code: string; name: string }) {
  const { data } = useDashboard(outletId);
  const shared = data?.shared_cash.balance;
  const alerts = data?.alerts.length ?? 0;
  const worstFeed = data?.providers.find((p) => p.feed_health.status !== "fresh");

  return (
    <tr className="border-t border-border hover:bg-subtle">
      <td className="px-3 py-2">
        <Link href={`/outlets/${outletId}`} className="font-medium text-accent hover:underline">
          {code}
        </Link>
        <p className="text-xs text-muted">{name}</p>
      </td>
      <td className="px-3 py-2 font-mono text-sm">{shared ? formatMoney(shared) : "—"}</td>
      <td className="px-3 py-2">
        {worstFeed && <FeedStatusDot status={worstFeed.feed_health.status as FeedHealthStatus} />}
      </td>
      <td className="px-3 py-2">{alerts > 0 ? <Badge tone="danger">{alerts}</Badge> : "—"}</td>
      <td className="px-3 py-2"><Badge tone="success">Active</Badge></td>
    </tr>
  );
}

export function OutletsOverviewView() {
  const { data, isLoading, error, refetch } = useOutlets();

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;
  if (!data?.length) return <EmptyState>No outlets</EmptyState>;

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-subtle text-left text-xs text-muted">
          <tr>
            <th className="px-3 py-2">Outlet</th>
            <th className="px-3 py-2">Shared cash</th>
            <th className="px-3 py-2">Feed</th>
            <th className="px-3 py-2">Alerts</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((o) => (
            <OutletRow key={o.outlet_id} outletId={o.outlet_id} code={o.synthetic_code} name={o.display_name} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
