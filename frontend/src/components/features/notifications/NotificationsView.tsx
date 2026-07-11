"use client";

import { useRouter } from "next/navigation";
import { useNotifications } from "@/lib/queries";
import { markNotificationRead } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queries";
import { EmptyState, ErrorState, Skeleton, Button, Card } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";

export function NotificationsView() {
  const router = useRouter();
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useNotifications();

  async function open(nid: string, caseId: string) {
    await markNotificationRead(nid);
    qc.invalidateQueries({ queryKey: queryKeys.notifications });
    router.push(`/cases/${caseId}`);
  }

  async function markAll() {
    const unread = data?.notifications.filter((n) => n.status !== "read") ?? [];
    await Promise.all(unread.map((n) => markNotificationRead(n.notification_id)));
    qc.invalidateQueries({ queryKey: queryKeys.notifications });
  }

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;

  const items = data?.notifications ?? [];

  return (
    <div className="space-y-4">
      {items.some((n) => n.status !== "read") && (
        <Button size="sm" onClick={markAll}>Mark all read</Button>
      )}
      {!items.length ? (
        <EmptyState>No notifications</EmptyState>
      ) : (
        items.map((n) => (
          <Card
            key={n.notification_id}
            className={`cursor-pointer transition hover:bg-subtle ${n.status !== "read" ? "border-accent/30 bg-accent/5" : ""}`}
            onClick={() => open(n.notification_id, n.case_id)}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm">{(n.payload.title as string) ?? "Case update"}</p>
              <span className="text-xs text-muted">{formatTime(n.queued_at)}</span>
            </div>
            <p className="mt-1 text-xs text-muted">View case →</p>
          </Card>
        ))
      )}
    </div>
  );
}
