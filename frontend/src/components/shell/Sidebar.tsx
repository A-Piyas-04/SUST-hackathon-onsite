"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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

function formatRoleName(user: Principal): string {
  const raw = roleLabel(user);
  return raw
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatScope(user: Principal): string {
  const scope = scopeLabel(user);
  if (!scope) return "Aggregate";
  return scope.charAt(0).toUpperCase() + scope.slice(1);
}

export function Sidebar({ collapsed }: { collapsed?: boolean }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useSession((s) => s.user);
  const logout = useSession((s) => s.logout);
  const { data: notifData } = useNotifications();
  if (!user) return null;
  const unread = notifData?.notifications.filter((n) => n.status !== "read").length ?? 0;
  const items = visibleNavItems(user);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-30 flex h-screen flex-col border-r border-border bg-background transition-[width]",
        collapsed ? "w-[var(--sidebar-collapsed)]" : "w-[var(--sidebar-width)]",
      )}
    >
      <div className="border-b border-border px-4 py-4">
        {!collapsed && (
          <>
            <p className="text-[13px] font-semibold text-maroon">{formatRoleName(user)}</p>
            <p className="mt-0.5 text-xs text-muted">{formatScope(user)}</p>
          </>
        )}
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {items.map((item) => {
          const Icon = ICONS[item.icon];
          const active =
            pathname === item.href ||
            pathname.startsWith(item.href + "/") ||
            (item.id === "dashboard" &&
              pathname.startsWith("/outlets/") &&
              !pathname.includes("/liquidity") &&
              !pathname.includes("/anomalies") &&
              !pathname.includes("/transactions") &&
              !pathname.includes("/data-quality"));
          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                "mb-0.5 flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition",
                active
                  ? "border-l-[3px] border-maroon bg-maroon-light font-semibold text-maroon"
                  : "border-l-[3px] border-transparent text-secondary hover:bg-surface hover:text-foreground",
                collapsed && "justify-center px-0",
              )}
              title={item.label}
            >
              {Icon && <Icon className={cn("h-4 w-4 shrink-0", active && "text-maroon")} />}
              {!collapsed && <span className="flex-1">{item.label}</span>}
              {!collapsed && item.id === "notifications" && unread > 0 && (
                <span className="rounded-full bg-danger px-1.5 text-[10px] text-white">
                  {unread > 99 ? "99+" : unread}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3">
        {!collapsed && (
          <>
            <p className="truncate px-1 text-[13px] text-muted">{user.display_name}</p>
            <button
              type="button"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
              className="mt-1 px-1 text-xs text-muted hover:text-maroon"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </aside>
  );
}

export function DemoBanner() {
  return (
    <div className="flex h-[var(--health-banner-height)] items-center justify-center bg-maroon-light text-xs font-medium text-maroon">
      Demo · Synthetic data
    </div>
  );
}
