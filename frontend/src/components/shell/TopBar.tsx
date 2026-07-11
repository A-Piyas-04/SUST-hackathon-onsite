"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useNotifications } from "@/lib/queries";
import { useSession } from "@/lib/session";
import type { FeedHealthStatus } from "@/lib/api";
import { FeedStatusDot } from "@/components/ui/FeedStatusDot";

export function TopBar({ title, breadcrumb }: { title: string; breadcrumb?: string }) {
  const user = useSession((s) => s.user);
  const { data } = useNotifications();
  const unread = data?.notifications.filter((n) => n.status !== "read").length ?? 0;

  return (
    <header className="flex h-[var(--topbar-height)] items-center justify-between border-b border-border bg-surface px-6">
      <div>
        <h1 className="text-base font-semibold">{title}</h1>
        {breadcrumb && <p className="text-xs text-muted">{breadcrumb}</p>}
      </div>
      <div className="flex items-center gap-3">
        <input
          disabled
          placeholder="Search"
          className="hidden w-48 rounded-md border border-border bg-elevated px-2 py-1 text-xs text-muted md:block"
        />
        <Link href="/notifications" className="relative rounded-md p-1.5 hover:bg-subtle">
          <Bell className="h-4 w-4 text-secondary" />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-0.5 text-[10px] text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </Link>
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-xs font-medium text-white">
          {user?.display_name?.charAt(0) ?? "?"}
        </div>
      </div>
    </header>
  );
}

export function HealthBanner({ issues }: { issues: { provider: string; status: FeedHealthStatus; detail?: string }[] }) {
  if (issues.length === 0) return null;
  const worst = issues[0];
  return (
    <div className="flex h-[var(--health-banner-height)] items-center gap-2 border-b border-warning/30 bg-warning/5 px-6 text-xs text-warning">
      <FeedStatusDot status={worst.status} />
      <span>
        {worst.provider} feed {worst.status}
        {worst.detail ? ` (${worst.detail})` : ""}
      </span>
    </div>
  );
}
