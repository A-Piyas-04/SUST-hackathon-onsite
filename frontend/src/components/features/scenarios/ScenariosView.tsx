"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  createFault,
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
import { Button, Card, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";

const FAULT_TYPES = ["delay", "missing_feed", "conflicting_balance"];

export function ScenariosView({ outletId }: { outletId: string }) {
  const router = useRouter();
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useScenarios();
  const [run, setRun] = useState<RunResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);

  function push(msg: string) {
    setLog((l) => [msg, ...l].slice(0, 10));
  }

  async function doRun(s: Scenario) {
    setBusy(s.code);
    try {
      const r = await startRun(s.code, outletId);
      setRun(r);
      push(`Started ${s.name}`);
      router.push("/dashboard");
    } catch (e) {
      push(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(null);
    }
  }

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;

  return (
    <div className="space-y-6">
      <Card>
        <p className="mb-3 text-sm font-medium">Scenarios</p>
        <div className="space-y-2">
          {data?.scenarios.filter((s) => s.code !== "normal").map((s) => (
            <div key={s.scenario_id} className="flex items-center justify-between border-t border-border py-2 first:border-0">
              <div>
                <p className="text-sm">{s.name}</p>
                <p className="text-xs text-muted">{s.description.slice(0, 80)}…</p>
              </div>
              <Button size="sm" disabled={busy !== null} onClick={() => doRun(s)}>Run</Button>
            </div>
          ))}
        </div>
      </Card>

      {run && (
        <Card>
          <p className="text-sm font-medium">Active run</p>
          <p className="text-xs text-muted">{run.scenario_code} · {run.status} · {run.artifacts.transactions} txns</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" onClick={async () => {
              const res = await runLiquidityAnalytics(run.simulation_run_id, outletId);
              push(`Liquidity: ${res.projections.length} projections`);
            }}>Liquidity analytics</Button>
            <Button size="sm" onClick={async () => {
              const res = await runAnomalyAnalytics(run.simulation_run_id, outletId);
              push(`Anomaly: ${res.flags.length} flags`);
            }}>Anomaly analytics</Button>
            <Button size="sm" onClick={async () => {
              const res = await publishAlerts(run.simulation_run_id, outletId);
              push(`Published ${res.published.length} alerts`);
            }}>Publish alerts</Button>
            <Button size="sm" variant="danger" onClick={async () => {
              await resetRun(run.simulation_run_id);
              setRun(null);
              push("Reset");
            }}>Reset</Button>
          </div>
        </Card>
      )}

      <Card>
        <p className="mb-2 text-sm font-medium">Fault injection</p>
        {FAULT_TYPES.map((ft) => (
          <div key={ft} className="flex items-center justify-between py-1 text-sm">
            <span className="capitalize">{ft.replace(/_/g, " ")}</span>
            <Button size="sm" disabled={!run} onClick={async () => {
              if (!run) return;
              const f = await createFault(run.simulation_run_id, { fault_type: ft, outlet_id: outletId });
              await toggleFault(run.simulation_run_id, f.fault_injection_id, true);
              push(`Enabled ${ft}`);
              qc.invalidateQueries({ queryKey: queryKeys.dataQuality(outletId) });
            }}>Enable</Button>
          </div>
        ))}
      </Card>

      {log.length > 0 && (
        <div className="text-xs text-muted">
          {log.map((l, i) => <p key={i}>{l}</p>)}
        </div>
      )}
    </div>
  );
}
