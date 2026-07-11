"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowLeftRight,
  BarChart3,
  Bell,
  FolderOpen,
  Inbox,
  LayoutDashboard,
  Play,
  ScrollText,
  Store,
  TrendingDown,
} from "lucide-react";
import type { Principal } from "@/lib/api";
import { roleLabel, scopeLabel, visibleNavItems } from "@/lib/authz";
import { useSession } from "@/lib/session";
import { useNotifications } from "@/lib/queries";
import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/primitives";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  Store,
  TrendingDown,
  AlertTriangle,
  Bell,
  FolderOpen,
  Inbox,
  ArrowLeftRight,
  Activity,
  Play,
  BarChart3,
  ScrollText,
};

export function Sidebar({ collapsed }: { collapsed?: boolean }) {
  const pathname = usePathname();
  const user = useSession((s) => s.user);
  const { data: notifData } = useNotifications();
  if (!user) return null;
  const unread = notifData?.notifications.filter((n) => n.status !== "read").length ?? 0;
  const items = visibleNavItems(user);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-border bg-surface transition-[width]",
        collapsed ? "w-[var(--sidebar-collapsed)]" : "w-[var(--sidebar-width)]",
      )}
    >
      <div className="border-b border-border px-3 py-4">
        {!collapsed && (
          <>
            <p className="text-sm font-semibold">Liquidity</p>
            <Badge tone="info">{roleLabel(user)}</Badge>
            <p className="mt-1 text-xs text-muted capitalize">{scopeLabel(user)}</p>
          </>
        )}
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {items.map((item) => {
          const Icon = ICONS[item.icon];
          const active =
            pathname === item.href ||
            pathname.startsWith(item.href + "/") ||
            (item.id === "dashboard" && pathname.startsWith("/outlets/") && !pathname.includes("/liquidity") && !pathname.includes("/anomalies") && !pathname.includes("/transactions") && !pathname.includes("/data-quality"));
          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                "mb-0.5 flex items-center gap-2 rounded-md px-2 py-2 text-sm transition",
                active ? "bg-accent/10 text-accent font-medium" : "text-secondary hover:bg-subtle hover:text-foreground",
                collapsed && "justify-center px-0",
              )}
              title={item.label}
            >
              {Icon && <Icon className="h-4 w-4 shrink-0" />}
              {!collapsed && <span className="flex-1">{item.label}</span>}
              {!collapsed && item.id === "notifications" && unread > 0 && (
                <span className="rounded-full bg-danger px-1.5 text-[10px] text-white">{unread > 99 ? "99+" : unread}</span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-2">
        {!collapsed && <p className="truncate px-2 text-xs text-muted">{user.display_name}</p>}
      </div>
    </aside>
  );
}

export function DemoBanner() {
  return (
    <div className="bg-warning/10 px-4 py-1 text-center text-xs text-warning">
      Demo · Synthetic data
    </div>
  );
}
