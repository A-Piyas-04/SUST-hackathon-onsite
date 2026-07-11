"use client";

import { useState } from "react";
import { fetchNotifications, markNotificationRead } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { AsyncView, Badge, Button, Card, EmptyState, formatDateTime } from "@/lib/ui";

export default function NotificationsPanel({ refreshKey }: { refreshKey: number }) {
  const [localKey, setLocalKey] = useState(0);
  const { state, reload } = useAsync(() => fetchNotifications(), [refreshKey, localKey]);
  const [busy, setBusy] = useState<string | null>(null);

  async function markRead(id: string) {
    setBusy(id);
    try {
      await markNotificationRead(id);
      setLocalKey((k) => k + 1);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Notifications</h2>
        <p className="text-xs text-zinc-500">In-app notifications routed to your role, with read / unread state.</p>
      </div>
      <AsyncView
        state={state}
        onRetry={reload}
        isEmpty={(d) => d.notifications.length === 0}
        empty={<EmptyState>No notifications for your role yet. They appear as cases are routed and escalated.</EmptyState>}
      >
        {(d) => (
          <ul className="space-y-2">
            {d.notifications.map((n) => {
              const unread = n.status !== "read";
              const title = (n.payload?.title_key as string) ?? (n.payload?.message as string) ?? "Case update";
              return (
                <li key={n.notification_id}>
                  <Card>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{String(title).replace(/[._]/g, " ")}</span>
                          {unread ? <Badge tone="blue">unread</Badge> : <Badge tone="slate">read</Badge>}
                        </div>
                        <p className="mt-1 text-xs text-zinc-500">
                          {n.recipient_role.replace(/_/g, " ")} · {n.channel} · {formatDateTime(n.queued_at)}
                        </p>
                      </div>
                      {unread && (
                        <Button size="sm" disabled={busy === n.notification_id} onClick={() => markRead(n.notification_id)}>
                          Mark read
                        </Button>
                      )}
                    </div>
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </AsyncView>
    </div>
  );
}
