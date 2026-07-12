"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  createFault,
  fetchDashboard,
  publishAlerts,
  resetRun,
  runAnomalyAnalytics,
  runLiquidityAnalytics,
  startRun,
  toggleFault,
  type RunResponse,
  type Scenario,
} from "@/lib/api";
import { useScenarios, queryKeys } from "@/lib/queries";
import { Button, Card, ErrorState, Skeleton, Toggle } from "@/components/ui/primitives";
import { cn } from "@/lib/cn";

const FAULT_TYPES = [
  { id: "delay", label: "Delay", desc: "Adds latency to provider feed delivery" },
  { id: "missing_feed", label: "Missing Feed", desc: "Stops incoming balance updates for a provider" },
  { id: "conflicting_balance", label: "Conflicting Balance", desc: "Injects a mismatched bKash balance snapshot" },
] as const;

const SCENARIO_STYLES: Record<string, { letter: string; border: string; badge: string; text: string }> = {
  scenario_a: {
    letter: "A",
    border: "var(--success)",
    badge: "bg-[var(--success-bg)] text-success",
    text: "var(--success)",
  },
  scenario_b: {
    letter: "B",
    border: "var(--warning)",
    badge: "bg-[var(--warning-bg)] text-warning",
    text: "var(--warning)",
  },
  scenario_c: {
    letter: "C",
    border: "var(--color-rocket)",
    badge: "bg-[rgba(107,37,120,0.1)] text-[var(--color-rocket)]",
    text: "var(--color-rocket)",
  },
  scenario_d: {
    letter: "D",
    border: "var(--maroon)",
    badge: "bg-maroon-light text-maroon",
    text: "var(--maroon)",
  },
};

type PipelineResult = {
  transactions: number;
  projections: number;
  flags: number;
  alerts: number;
};

export function ScenariosView({ outletId }: { outletId: string }) {
  const router = useRouter();
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useScenarios();
  const [run, setRun] = useState<RunResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [faults, setFaults] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<PipelineResult | null>(null);

  function push(msg: string) {
    setLog((l) => [msg, ...l].slice(0, 12));
  }

  async function refreshScenarioState() {
    // Refresh all derived views and eagerly replace the stable dashboard
    // snapshot so navigation cannot briefly show balances from the prior run.
    await qc.invalidateQueries({
      predicate: (query) => query.queryKey[0] !== "dashboard",
    });
    await qc.invalidateQueries({ queryKey: queryKeys.dashboard(outletId) });
    const dashboard = await fetchDashboard(outletId);
    qc.setQueryData(queryKeys.dashboard(outletId), dashboard);
  }

  // Running a scenario is a 4-stage pipeline: generate synthetic data → compute
  // liquidity projections → detect unusual activity → publish alerts (which may
  // open cases). The backend does NOT chain these automatically, so we
  // orchestrate them here and stream progress. Previously this only ran stage 1
  // and immediately navigated to the dashboard, so no alerts/projections were
  // ever produced and it looked like nothing happened.
  async function doRun(s: Scenario) {
    setBusy(s.code);
    setResult(null);
    setLog([]);
    try {
      push(`Starting "${s.name}"…`);
      const r = await startRun(s.code, outletId);
      setRun(r);
      push(`Generated ${r.artifacts.transactions} transactions and ${r.artifacts.provider_snapshots} balance snapshots`);

      push("Computing liquidity projections…");
      const liq = await runLiquidityAnalytics(r.simulation_run_id, outletId);
      push(`→ ${liq.projections.length} liquidity projection(s)`);

      push("Detecting unusual activity…");
      const anom = await runAnomalyAnalytics(r.simulation_run_id, outletId);
      push(`→ ${anom.flags.length} anomaly flag(s)`);

      push("Publishing alerts…");
      const pub = await publishAlerts(r.simulation_run_id, outletId);
      push(`→ ${pub.published.length} alert(s) published`);

      await refreshScenarioState();

      setResult({
        transactions: r.artifacts.transactions,
        projections: liq.projections.length,
        flags: anom.flags.length,
        alerts: pub.published.length,
      });
      push(`Done — "${s.name}" is ready. Open the dashboard or alerts to see the outcome.`);

    } catch (e) {
      push(`Failed: ${e instanceof Error ? e.message : "run error"}`);
    } finally {
      setBusy(null);
    }
  }

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;

  return (
    <div className="space-y-6">
      <Card className="p-0">
        <p className="section-heading border-b border-border px-5 py-4">Scenarios</p>
        <div>
          {data?.scenarios
            .filter((s) => s.code !== "normal")
            .map((s) => {
              const style = SCENARIO_STYLES[s.code] ?? SCENARIO_STYLES.scenario_a;
              const isRunning = busy === s.code;
              const isActive = run?.scenario_code === s.code;
              return (
                <div
                  key={s.scenario_id}
                  className="flex flex-col gap-3 border-b border-border px-5 py-4 last:border-b-0 hover:bg-surface sm:flex-row sm:items-center sm:justify-between"
                  style={{ borderLeftWidth: 3, borderLeftColor: style.border, borderLeftStyle: "solid" }}
                >
                  <div className="flex min-w-0 flex-1 items-start gap-3">
                    <span
                      className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-mono text-sm font-bold",
                        style.badge,
                      )}
                    >
                      {style.letter}
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-foreground">{s.name}</p>
                        {isActive && (
                          <span className="text-xs font-medium text-maroon">Active run</span>
                        )}
                      </div>
                      <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-muted">{s.description}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="primary"
                    disabled={busy !== null && !isRunning}
                    onClick={() => doRun(s)}
                    className="shrink-0 px-5"
                  >
                    {isRunning ? (
                      <span className="inline-flex items-center gap-2">
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        Running…
                      </span>
                    ) : (
                      "Run"
                    )}
                  </Button>
                </div>
              );
            })}
        </div>
      </Card>

      {run && (
        <Card>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="section-heading">Active run</p>
              <p className="mt-1 text-xs text-muted">
                {run.scenario_code} · {busy ? "running…" : "completed"}
              </p>
            </div>
            <Button
              size="sm"
              variant="danger"
              disabled={busy !== null}
              onClick={async () => {
                await resetRun(run.simulation_run_id);
                setRun(null);
                setResult(null);
                setFaults({});
                push("Reset run — data cleared");
                await refreshScenarioState();
              }}
            >
              Reset
            </Button>
          </div>

          {result && (
            <>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { label: "Transactions", value: result.transactions },
                  { label: "Projections", value: result.projections },
                  { label: "Anomaly flags", value: result.flags },
                  { label: "Alerts", value: result.alerts },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-lg border border-border bg-surface px-3 py-2">
                    <p className="text-lg font-semibold tabular-nums text-foreground">{stat.value}</p>
                    <p className="text-xs text-muted">{stat.label}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button size="sm" variant="primary" onClick={() => router.push("/dashboard")}>
                  View dashboard
                </Button>
                <Button size="sm" onClick={() => router.push("/alerts")}>
                  View alerts{result.alerts > 0 ? ` (${result.alerts})` : ""}
                </Button>
                {result.alerts > 0 && (
                  <Button size="sm" onClick={() => router.push("/cases")}>
                    View cases
                  </Button>
                )}
              </div>
            </>
          )}
        </Card>
      )}

      <Card className="p-0">
        <div className="border-b border-border px-5 py-4">
          <p className="section-heading">Fault injection</p>
          <p className="mt-1 text-xs text-muted">Enabling faults affects data confidence for this session.</p>
        </div>
        {FAULT_TYPES.map((ft) => {
          const enabled = faults[ft.id] ?? false;
          return (
            <div
              key={ft.id}
              className={cn(
                "flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-b-0",
                enabled && "bg-[var(--danger-bg)]",
              )}
              style={
                enabled
                  ? { borderLeftWidth: 3, borderLeftColor: "var(--danger)", borderLeftStyle: "solid" }
                  : undefined
              }
            >
              <div>
                <p className="text-sm text-foreground">{ft.label}</p>
                <p className="mt-0.5 text-xs text-muted">{ft.desc}</p>
              </div>
              <Toggle
                checked={enabled}
                disabled={!run}
                onChange={async (on) => {
                  if (!run) return;
                  if (on) {
                    const f = await createFault(run.simulation_run_id, {
                      fault_type: ft.id,
                      outlet_id: outletId,
                      // The compact demo control has no provider selector.
                      // Scope balance conflicts to one provider so the other
                      // cards continue to demonstrate normal balance movement.
                      parameters: ft.id === "conflicting_balance" ? { target_provider: "bkash" } : undefined,
                    });
                    await toggleFault(run.simulation_run_id, f.fault_injection_id, true);
                    push(`Enabled ${ft.label}`);
                  } else {
                    push(`Disabled ${ft.label}`);
                  }
                  setFaults((prev) => ({ ...prev, [ft.id]: on }));
                  qc.invalidateQueries({ queryKey: queryKeys.dataQuality(outletId) });
                }}
              />
            </div>
          );
        })}
      </Card>

      {log.length > 0 && (
        <div className="font-mono text-xs text-muted">
          {log.map((l, i) => (
            <p key={i}>{l}</p>
          ))}
        </div>
      )}
    </div>
  );
}
