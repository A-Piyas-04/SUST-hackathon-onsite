"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useNotifications } from "@/lib/queries";
import { useSession } from "@/lib/session";
import type { FeedHealthStatus } from "@/lib/api";
import { FeedStatusDot } from "@/components/ui/FeedStatusDot";
import { providerDisplayName } from "@/lib/format";

export function TopBar({ title, breadcrumb }: { title: string; breadcrumb?: string }) {
  const user = useSession((s) => s.user);
  const { data } = useNotifications();
  const unread = data?.notifications.filter((n) => n.status !== "read").length ?? 0;
  const initials = user?.display_name?.charAt(0)?.toUpperCase() ?? "?";

  return (
    <header className="flex h-[var(--topbar-height)] items-center justify-between border-b border-border bg-background px-7">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        {breadcrumb && <p className="text-xs text-muted">{breadcrumb}</p>}
      </div>
      <div className="flex items-center gap-3">
        <Link href="/notifications" className="relative rounded-md p-1.5 hover:bg-surface">
          <Bell className="h-4 w-4 text-secondary" />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-0.5 text-[10px] text-white">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </Link>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-maroon text-xs font-semibold text-white">
          {initials}
        </div>
      </div>
    </header>
  );
}

export function HealthBanner({
  issues,
}: {
  issues: { provider: string; status: FeedHealthStatus; detail?: string }[];
}) {
  if (issues.length === 0) return null;
  const worst = issues[0];
  return (
    <div className="flex h-[var(--health-banner-height)] items-center gap-2 border-b border-warning/30 bg-warning-bg px-7 text-xs text-warning">
      <FeedStatusDot status={worst.status} />
      <span>
        {providerDisplayName(worst.provider)} feed {worst.status}
        {worst.detail ? ` (${worst.detail})` : ""}
      </span>
    </div>
  );
}
