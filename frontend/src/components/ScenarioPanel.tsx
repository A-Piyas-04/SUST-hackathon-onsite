"use client";

import { useState } from "react";
import {
  ApiError,
  createFault,
  fetchProviders,
  fetchScenarios,
  FaultSummary,
  publishAlerts,
  ProviderRef,
  resetRun,
  runAnomalyAnalytics,
  runLiquidityAnalytics,
  RunResponse,
  Scenario,
  startRun,
  toggleFault,
} from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { AsyncView, Badge, Button, Card, formatDateTime } from "@/lib/ui";

const FAULT_TYPES = ["conflicting_balance", "delay", "missing_feed", "missing_field", "malformed_payload"];

type LogEntry = { at: string; text: string; tone: "ok" | "err" };

export default function ScenarioPanel({
  outletId,
  bump,
}: {
  outletId: string;
  bump: () => void;
}) {
  const scenarios = useAsync(() => fetchScenarios(), []);
  const providers = useAsync(() => fetchProviders(), []);

  const [run, setRun] = useState<RunResponse | null>(null);
  const [seeds, setSeeds] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [faultType, setFaultType] = useState(FAULT_TYPES[0]);
  const [faultProvider, setFaultProvider] = useState("");

  function push(text: string, tone: "ok" | "err" = "ok") {
    setLog((l) => [{ at: new Date().toISOString(), text, tone }, ...l].slice(0, 20));
  }

  async function guard(key: string, fn: () => Promise<void>) {
    setBusy(key);
    try {
      await fn();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Action failed";
      push(msg, "err");
    } finally {
      setBusy(null);
      bump();
    }
  }

  function doRun(s: Scenario) {
    const raw = seeds[s.code] ?? String(s.default_seed);
    const seed = Number(raw);
    guard(`run-${s.code}`, async () => {
      const r = await startRun(s.code, outletId, Number.isFinite(seed) ? seed : undefined);
      setRun(r);
      push(
        `Ran ${s.code} (seed ${r.seed}) → ${r.status}, ${r.artifacts.transactions} txns, ${r.artifacts.provider_snapshots} provider snapshots`,
        r.artifacts.transactions > 0 ? "ok" : "err",
      );
      if (r.artifacts.transactions === 0)
        push("No new transactions — this seed was already ingested. Randomize the seed (🎲) or reset the DB.", "err");
    });
  }

  function doLiquidity() {
    if (!run) return;
    guard("liquidity", async () => {
      const res = await runLiquidityAnalytics(run.simulation_run_id, outletId);
      push(`Liquidity analytics: ${res.projections.length} projections, ${res.candidates.length} alertable candidate(s)`);
    });
  }
  function doAnomaly() {
    if (!run) return;
    guard("anomaly", async () => {
      const res = await runAnomalyAnalytics(run.simulation_run_id, outletId);
      push(
        `Anomaly analytics: ${res.flags.length} flag(s), ${res.suppressed_count} suppressed, ${res.candidates.length} alertable candidate(s)`,
      );
    });
  }
  function doPublish() {
    if (!run) return;
    guard("publish", async () => {
      const res = await publishAlerts(run.simulation_run_id, outletId);
      push(`Published ${res.published.length} alert(s), ${res.deduplicated_alert_ids.length} deduplicated`);
    });
  }
  function doReset() {
    if (!run) return;
    guard("reset", async () => {
      const r = await resetRun(run.simulation_run_id);
      setRun(r);
      push(`Reset run → status ${r.status}`);
    });
  }
  function doAddFault() {
    if (!run) return;
    const provider_id = faultProvider || null;
    guard("fault-add", async () => {
      const f = await createFault(run.simulation_run_id, {
        fault_type: faultType,
        outlet_id: outletId,
        provider_id,
        parameters: {},
      });
      setRun({ ...run, faults: [...run.faults, f] });
      push(`Added fault ${f.fault_type}${provider_id ? " on provider" : ""} (enabled=${f.is_enabled})`);
    });
  }
  function doToggleFault(f: FaultSummary) {
    if (!run) return;
    guard(`fault-${f.fault_injection_id}`, async () => {
      const updated = await toggleFault(run.simulation_run_id, f.fault_injection_id, !f.is_enabled);
      setRun({
        ...run,
        faults: run.faults.map((x) => (x.fault_injection_id === updated.fault_injection_id ? updated : x)),
      });
      push(`Toggled fault ${updated.fault_type} → enabled=${updated.is_enabled}`);
    });
  }

  const providerList: ProviderRef[] = providers.state.kind === "ready" ? providers.state.data : [];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Scenarios &amp; faults</h2>
        <p className="text-xs text-zinc-500">
          Drive the deterministic demo: run a scenario, trigger analytics, inject faults, then publish alertable
          candidates. Seeds are prefilled with each scenario&apos;s deterministic default.
        </p>
      </div>

      <AsyncView state={scenarios.state} onRetry={scenarios.reload}>
        {(d) => (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {d.scenarios.map((s) => (
              <Card key={s.code} title={s.name} subtitle={s.description}>
                <div className="flex items-center gap-2">
                  <input
                    className="w-28 rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-900"
                    value={seeds[s.code] ?? String(s.default_seed)}
                    onChange={(e) => setSeeds((p) => ({ ...p, [s.code]: e.target.value }))}
                    aria-label={`Seed for ${s.code}`}
                  />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSeeds((p) => ({ ...p, [s.code]: String(Math.floor(Math.random() * 1e9)) }))}
                    title="Randomize seed to avoid dedup on repeated runs"
                  >
                    🎲
                  </Button>
                  <Button size="sm" variant="primary" disabled={busy === `run-${s.code}`} onClick={() => doRun(s)}>
                    {busy === `run-${s.code}` ? "Running…" : "Run"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </AsyncView>

      {run && (
        <Card
          title="Active run"
          subtitle={`${run.scenario_code} · seed ${run.seed}`}
          right={<Badge tone={run.status === "completed" ? "green" : "amber"}>{run.status}</Badge>}
        >
          <p className="text-xs text-zinc-500">
            {run.simulation_run_id} · {run.artifacts.transactions} txns · started {formatDateTime(run.started_at)}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" disabled={busy === "liquidity"} onClick={doLiquidity}>
              Run liquidity analytics
            </Button>
            <Button size="sm" disabled={busy === "anomaly"} onClick={doAnomaly}>
              Run anomaly analytics
            </Button>
            <Button size="sm" variant="primary" disabled={busy === "publish"} onClick={doPublish}>
              Publish alertable candidates
            </Button>
            <Button size="sm" variant="ghost" disabled={busy === "reset"} onClick={doReset}>
              Reset run
            </Button>
          </div>

          {/* Fault controls for live Scenario C demonstration */}
          <div className="mt-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
            <p className="mb-2 text-xs font-medium text-zinc-500">Fault injection (degraded-feed demo)</p>
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-900"
                value={faultType}
                onChange={(e) => setFaultType(e.target.value)}
              >
                {FAULT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <select
                className="rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-900"
                value={faultProvider}
                onChange={(e) => setFaultProvider(e.target.value)}
              >
                <option value="">outlet-wide</option>
                {providerList.map((p) => (
                  <option key={p.provider_id} value={p.provider_id}>
                    {p.display_name}
                  </option>
                ))}
              </select>
              <Button size="sm" disabled={busy === "fault-add"} onClick={doAddFault}>
                Add fault
              </Button>
            </div>
            {run.faults.length > 0 && (
              <ul className="mt-2 space-y-1">
                {run.faults.map((f) => (
                  <li key={f.fault_injection_id} className="flex items-center justify-between gap-2 text-xs">
                    <span>
                      {f.fault_type} {f.provider_id ? "· provider-scoped" : "· outlet-wide"}{" "}
                      <Badge tone={f.is_enabled ? "amber" : "slate"}>{f.is_enabled ? "enabled" : "disabled"}</Badge>
                    </span>
                    <Button size="sm" variant="ghost" onClick={() => doToggleFault(f)}>
                      {f.is_enabled ? "Disable" : "Enable"}
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-xs text-zinc-400">
              After changing faults, re-run the scenario and analytics to see confidence drop / alerts suppress.
            </p>
          </div>
        </Card>
      )}

      {log.length > 0 && (
        <Card title="Action log">
          <ul className="space-y-1 text-xs">
            {log.map((e, i) => (
              <li key={i} className={e.tone === "err" ? "text-red-600 dark:text-red-400" : "text-zinc-600 dark:text-zinc-300"}>
                <span className="text-zinc-400">{new Date(e.at).toLocaleTimeString()}</span> · {e.text}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
