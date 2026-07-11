/**
 * Client-side authorization — mirrors GET /api/v1/me permissions.
 */

import type { AppRole, Principal } from "./api";

export type NavItemId =
  | "dashboard"
  | "outlets"
  | "liquidity"
  | "anomalies"
  | "alerts"
  | "cases"
  | "notifications"
  | "transactions"
  | "data-quality"
  | "scenarios"
  | "metrics"
  | "audit";

export type CaseActionId =
  | "open"
  | "assign"
  | "acknowledge"
  | "escalate"
  | "resolve"
  | "note"
  | "review";

const NAV_PERMISSION: Record<NavItemId, string> = {
  dashboard: "tab:dashboard",
  outlets: "tab:dashboard",
  liquidity: "tab:liquidity",
  anomalies: "tab:anomalies",
  alerts: "tab:alerts",
  cases: "tab:cases",
  notifications: "tab:notifications",
  transactions: "tab:dashboard",
  "data-quality": "tab:dashboard",
  scenarios: "tab:scenarios",
  metrics: "tab:validation",
  audit: "tab:cases",
};

const CASE_ACTION_PERMISSION: Record<CaseActionId, string> = {
  open: "case:open",
  assign: "case:assign",
  acknowledge: "case:acknowledge",
  escalate: "case:escalate",
  resolve: "case:resolve",
  note: "case:note",
  review: "case:review",
};

export const NAV_ITEMS: { id: NavItemId; label: string; href: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { id: "outlets", label: "Outlets", href: "/outlets", icon: "Store" },
  { id: "liquidity", label: "Liquidity", href: "/liquidity", icon: "TrendingDown" },
  { id: "anomalies", label: "Anomalies", href: "/anomalies", icon: "AlertTriangle" },
  { id: "alerts", label: "Alerts", href: "/alerts", icon: "Bell" },
  { id: "cases", label: "Cases", href: "/cases", icon: "FolderOpen" },
  { id: "notifications", label: "Notifications", href: "/notifications", icon: "Inbox" },
  { id: "transactions", label: "Transactions", href: "/transactions", icon: "ArrowLeftRight" },
  { id: "data-quality", label: "Data Quality", href: "/data-quality", icon: "Activity" },
  { id: "scenarios", label: "Scenarios", href: "/scenarios", icon: "Play" },
  { id: "metrics", label: "Metrics", href: "/metrics", icon: "BarChart3" },
  { id: "audit", label: "Audit", href: "/audit", icon: "ScrollText" },
];

export function hasPermission(user: Principal, permission: string): boolean {
  if (user.permissions?.includes(permission)) return true;
  return fallbackPermission(user.roles, permission);
}

function fallbackPermission(roles: AppRole[], permission: string): boolean {
  const isAdmin = roles.includes("admin");
  if (isAdmin) return true;
  if (permission === "tab:notifications") return true;

  if (roles.includes("management")) {
    return [
      "tab:dashboard",
      "tab:liquidity",
      "tab:anomalies",
      "tab:alerts",
      "tab:cases",
      "tab:notifications",
      "tab:validation",
      "tab:scenarios",
    ].includes(permission);
  }

  if (roles.includes("agent")) {
    return [
      "tab:dashboard",
      "tab:alerts",
      "tab:cases",
      "tab:notifications",
      "case:note",
    ].includes(permission);
  }

  if (roles.includes("risk_analyst")) {
    return !permission.startsWith("simulation:") && !permission.startsWith("tab:scenarios");
  }

  if (roles.some((r) => r === "field_officer" || r === "area_manager" || r === "provider_ops")) {
    if (permission === "tab:validation") return false;
    return !permission.startsWith("simulation:") && !permission.startsWith("tab:scenarios");
  }

  return false;
}

export function canSeeNav(user: Principal, item: NavItemId): boolean {
  if (item === "outlets" && user.roles.includes("agent")) return false;
  if (item === "audit" && user.roles.includes("agent")) return false;
  if (item === "liquidity" && user.roles.includes("agent")) {
    return hasPermission(user, "tab:liquidity");
  }
  if (item === "anomalies" && user.roles.includes("agent")) return false;
  if (item === "scenarios") return hasPermission(user, "tab:scenarios") || user.roles.includes("management");
  if (item === "metrics") return hasPermission(user, "tab:validation");
  return hasPermission(user, NAV_PERMISSION[item]);
}

export function visibleNavItems(user: Principal) {
  return NAV_ITEMS.filter((n) => canSeeNav(user, n.id));
}

export function canPerformCaseAction(user: Principal, action: CaseActionId): boolean {
  return hasPermission(user, CASE_ACTION_PERMISSION[action]);
}

export function canSwitchOutlet(user: Principal): boolean {
  return hasPermission(user, "outlet:switch");
}

export function lockedOutletId(user: Principal): string | null {
  if (canSwitchOutlet(user)) return null;
  const scope = user.scopes.find((s) => s.outlet_id);
  return scope?.outlet_id ?? null;
}

export function canManageSimulation(user: Principal): boolean {
  return hasPermission(user, "simulation:manage");
}

export function canOpenCase(user: Principal): boolean {
  return canPerformCaseAction(user, "open");
}

export function isReadOnlyCases(user: Principal): boolean {
  return user.roles.includes("management") && !canPerformCaseAction(user, "acknowledge");
}

export function roleLabel(user: Principal): string {
  const role = user.roles[0]?.replace(/_/g, " ") ?? "user";
  return role;
}

export function scopeLabel(user: Principal): string {
  const s = user.scopes[0];
  if (!s) return "";
  if (s.outlet_id) return "outlet";
  if (s.area_id) return "area";
  if (s.provider_id) return "provider";
  return "aggregate";
}

export function canAccessRoute(user: Principal, pathname: string): boolean {
  if (pathname.startsWith("/login")) return true;
  if (pathname === "/dashboard" || pathname.startsWith("/outlets/")) {
    return canSeeNav(user, "dashboard") || canSeeNav(user, "outlets");
  }
  if (pathname === "/outlets") return canSeeNav(user, "outlets");
  if (pathname.startsWith("/liquidity") || pathname.includes("/liquidity")) return canSeeNav(user, "liquidity");
  if (pathname.startsWith("/anomalies") || pathname.includes("/anomalies")) return canSeeNav(user, "anomalies");
  if (pathname.startsWith("/alerts")) return canSeeNav(user, "alerts");
  if (pathname.startsWith("/cases")) return canSeeNav(user, "cases") || canSeeNav(user, "audit");
  if (pathname.startsWith("/notifications")) return canSeeNav(user, "notifications");
  if (pathname.startsWith("/transactions") || pathname.includes("/transactions")) return canSeeNav(user, "transactions");
  if (pathname.startsWith("/data-quality") || pathname.includes("/data-quality")) return canSeeNav(user, "data-quality");
  if (pathname.startsWith("/scenarios")) return canSeeNav(user, "scenarios");
  if (pathname.startsWith("/metrics")) return canSeeNav(user, "metrics");
  if (pathname.startsWith("/audit")) return canSeeNav(user, "audit");
  return true;
}

export const DEFAULT_OUTLET = "0b000000-0000-0000-0000-000000000001";
