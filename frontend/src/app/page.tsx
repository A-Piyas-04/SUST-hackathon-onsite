"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchMe,
  fetchOutlets,
  getApiBaseUrl,
  OutletListItem,
  Principal,
  setToken,
  updatePreferences,
} from "@/lib/api";
import {
  canSeeTab,
  defaultTab,
  lockedOutletId,
  TabId,
  visibleTabs,
} from "@/lib/authz";
import { Badge, Button, LOCALE_LABELS, Spinner } from "@/lib/ui";
import LoginPanel from "@/components/LoginPanel";
import OutletDashboard from "@/components/OutletDashboard";
import LiquidityPanel from "@/components/LiquidityPanel";
import AnomalyPanel from "@/components/AnomalyPanel";
import ScenarioPanel from "@/components/ScenarioPanel";
import AlertsPanel from "@/components/AlertsPanel";
import CasePanel from "@/components/CasePanel";
import NotificationsPanel from "@/components/NotificationsPanel";
import ValidationPanel from "@/components/ValidationPanel";

const DEFAULT_OUTLET = "0b000000-0000-0000-0000-000000000001";

const TAB_LABELS: Record<TabId, string> = {
  dashboard: "Dashboard",
  liquidity: "Liquidity",
  anomalies: "Anomalies",
  scenarios: "Scenarios & Faults",
  alerts: "Alerts",
  cases: "Cases",
  validation: "Validation Evidence",
  notifications: "Notifications",
};

function scopeLabel(p: Principal): string {
  const s = p.scopes[0];
  if (!s) return "no scope";
  const parts: string[] = [];
  if (s.provider_id) parts.push("provider-scoped");
  if (s.area_id) parts.push("area-scoped");
  if (s.outlet_id) parts.push("outlet-scoped");
  if (parts.length === 0) parts.push("cross-provider");
  return parts.join(" · ");
}

export default function Home() {
  const [booting, setBooting] = useState(true);
  const [user, setUser] = useState<Principal | null>(null);
  const [tab, setTab] = useState<TabId>("dashboard");
  const [outletId, setOutletId] = useState(DEFAULT_OUTLET);
  const [outlets, setOutlets] = useState<OutletListItem[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedCase, setSelectedCase] = useState<string | null>(null);

  const bump = useCallback(() => setRefreshKey((k) => k + 1), []);

  const allowedTabs = useMemo(() => (user ? visibleTabs(user) : []), [user]);

  // Restore session on load.
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const me = await fetchMe();
        if (active) {
          setUser(me);
          setTab(defaultTab(me));
          const locked = lockedOutletId(me);
          if (locked) setOutletId(locked);
        }
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setBooting(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchOutlets()
      .then((list) => {
        setOutlets(list);
        const locked = lockedOutletId(user);
        if (locked) {
          setOutletId(locked);
        } else if (list.length > 0 && !list.some((o) => o.outlet_id === outletId)) {
          setOutletId(list[0].outlet_id);
        }
      })
      .catch(() => setOutlets([]));
  }, [user]);

  useEffect(() => {
    if (!user) return;
    if (!canSeeTab(user, tab) && allowedTabs.length > 0) {
      setTab(allowedTabs[0]);
    }
  }, [user, tab, allowedTabs]);

  function handleLogin(me: Principal) {
    setUser(me);
    setTab(defaultTab(me));
    const locked = lockedOutletId(me);
    if (locked) setOutletId(locked);
  }

  function logout() {
    setToken(null);
    setUser(null);
    setTab("dashboard");
  }

  async function changeLocale(locale: "en" | "bn" | "bn_latn") {
    try {
      const updated = await updatePreferences(locale);
      setUser(updated);
    } catch {
      /* non-blocking */
    }
  }

  function openCaseFromAlert(caseId: string) {
    setSelectedCase(caseId);
    setTab("cases");
    bump();
  }

  if (booting) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Connecting to backend…" />
      </div>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen px-4">
        <LoginPanel onLogin={handleLogin} />
      </main>
    );
  }

  const showOutletPicker = outlets.length > 0 && lockedOutletId(user) === null;

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div>
            <p className="text-sm font-semibold">Liquidity &amp; Coordination Platform</p>
            <p className="text-xs text-zinc-500">
              Decision-support demo · <span className="font-mono">{getApiBaseUrl()}</span>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium">{user.display_name}</p>
              <p className="text-xs text-zinc-500">
                <Badge tone="violet">{user.roles.join(", ")}</Badge> <span className="ml-1">{scopeLabel(user)}</span>
              </p>
            </div>
            <div className="flex gap-1">
              {(["en", "bn", "bn_latn"] as const).map((l) => (
                <Button
                  key={l}
                  size="sm"
                  variant={user.preferred_locale === l ? "primary" : "ghost"}
                  onClick={() => changeLocale(l)}
                >
                  {LOCALE_LABELS[l]}
                </Button>
              ))}
            </div>
            <Button size="sm" onClick={logout}>
              Log out
            </Button>
          </div>
        </div>

        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-2">
          {allowedTabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm transition ${
                tab === t
                  ? "border-zinc-900 font-medium dark:border-white"
                  : "border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
              }`}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        {showOutletPicker && (
          <div className="mb-4 flex items-center gap-2 text-sm">
            <label className="text-xs text-zinc-500">Outlet</label>
            <select
              className="rounded border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              value={outletId}
              onChange={(e) => setOutletId(e.target.value)}
            >
              {outlets.map((o) => (
                <option key={o.outlet_id} value={o.outlet_id}>
                  {o.synthetic_code} — {o.display_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {tab === "dashboard" && <OutletDashboard outletId={outletId} refreshKey={refreshKey} />}
        {tab === "liquidity" && <LiquidityPanel outletId={outletId} refreshKey={refreshKey} user={user} />}
        {tab === "anomalies" && <AnomalyPanel outletId={outletId} refreshKey={refreshKey} user={user} />}
        {tab === "scenarios" && <ScenarioPanel outletId={outletId} bump={bump} user={user} />}
        {tab === "alerts" && (
          <AlertsPanel outletId={outletId} refreshKey={refreshKey} onOpenedCase={openCaseFromAlert} user={user} />
        )}
        {tab === "cases" && (
          <CasePanel refreshKey={refreshKey} selectedCaseId={selectedCase} onSelect={setSelectedCase} user={user} />
        )}
        {tab === "validation" && <ValidationPanel refreshKey={refreshKey} />}
        {tab === "notifications" && <NotificationsPanel refreshKey={refreshKey} />}
      </main>
    </div>
  );
}
