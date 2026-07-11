/**
 * Client-side authorization helpers for the demo shell.
 * Backend policy remains authoritative; these mirror GET /api/v1/me permissions.
 */

import type { AppRole, Principal } from "./api";

export type TabId =
  | "dashboard"
  | "liquidity"
  | "anomalies"
  | "scenarios"
  | "alerts"
  | "cases"
  | "notifications"
  | "validation";

export type CaseActionId =
  | "open"
  | "assign"
  | "acknowledge"
  | "escalate"
  | "resolve"
  | "note"
  | "review";

const TAB_PERMISSION: Record<TabId, string> = {
  dashboard: "tab:dashboard",
  liquidity: "tab:liquidity",
  anomalies: "tab:anomalies",
  scenarios: "tab:scenarios",
  alerts: "tab:alerts",
  cases: "tab:cases",
  notifications: "tab:notifications",
  validation: "tab:validation",
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
      "tab:alerts",
      "tab:cases",
      "tab:notifications",
      "tab:validation",
    ].includes(permission);
  }
  if (roles.includes("agent")) {
    return [
      "tab:dashboard",
      "tab:liquidity",
      "tab:anomalies",
      "tab:alerts",
      "tab:cases",
      "tab:notifications",
      "case:note",
    ].includes(permission);
  }
  if (roles.includes("risk_analyst")) {
    if (permission === "tab:validation") return false;
    return !permission.startsWith("simulation:") && !permission.startsWith("tab:scenarios");
  }
  if (roles.some((r) => r === "field_officer" || r === "area_manager" || r === "provider_ops")) {
    if (permission === "tab:validation") return false;
    return !permission.startsWith("simulation:") && !permission.startsWith("tab:scenarios");
  }
  return false;
}

export function canSeeTab(user: Principal, tab: TabId): boolean {
  return hasPermission(user, TAB_PERMISSION[tab]);
}

export function visibleTabs(user: Principal): TabId[] {
  const order: TabId[] = [
    "dashboard",
    "liquidity",
    "anomalies",
    "scenarios",
    "alerts",
    "cases",
    "validation",
    "notifications",
  ];
  return order.filter((tab) => canSeeTab(user, tab));
}

export function canSeeValidation(user: Principal): boolean {
  return canSeeTab(user, "validation");
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

export function defaultTab(user: Principal): TabId {
  const tabs = visibleTabs(user);
  if (tabs.includes("scenarios") && user.roles.includes("admin")) return "scenarios";
  if (tabs.includes("cases") && user.roles.some((r) => r === "provider_ops" || r === "area_manager" || r === "risk_analyst")) {
    return "cases";
  }
  return tabs[0] ?? "dashboard";
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
