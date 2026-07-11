"use client";

import { useState } from "react";
import {
  Alert,
  AlertExplanation,
  fetchAlert,
  fetchAlertExplanations,
  fetchAlerts,
  LocaleCode,
  openCase,
  Principal,
} from "@/lib/api";
import { canOpenCase } from "@/lib/authz";
import { useAsync } from "@/lib/hooks";
import {
  AsyncView,
  Badge,
  Button,
  Card,
  EmptyState,
  formatDateTime,
  LOCALE_LABELS,
  SeverityBadge,
} from "@/lib/ui";

const LOCALES: LocaleCode[] = ["en", "bn", "bn_latn"];

function alertTitle(a: Alert): string {
  const map: Record<string, string> = {
    "alert.anomaly.unusual_activity": "Unusual activity — requires review",
    "alert.liquidity.shared_cash_shortage": "Shared cash shortage — requires review",
  };
  return map[a.title_key] ?? a.title_key.replace(/[._]/g, " ");
}

function ExplanationBlock({ e }: { e: AlertExplanation }) {
  const rows: [string, string | null][] = [
    ["Situation", e.situation_text],
    ["Evidence", e.evidence_text],
    ["Uncertainty", e.uncertainty_text],
    ["Next step", e.next_step_text],
    ["Benign context", e.benign_context_text],
  ];
  return (
    <div className="space-y-2">
      {rows.map(([label, text]) =>
        text ? (
          <div key={label}>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">{label}</p>
            <p className="text-sm">{text}</p>
          </div>
        ) : null,
      )}
    </div>
  );
}

function AlertDetail({
  alertId,
  refreshKey,
  onOpenedCase,
  user,
}: {
  alertId: string;
  refreshKey: number;
  onOpenedCase: (caseId: string) => void;
  user: Principal;
}) {
  const alert = useAsync(() => fetchAlert(alertId), [alertId, refreshKey]);
  const explanations = useAsync(() => fetchAlertExplanations(alertId), [alertId, refreshKey]);
  const [locale, setLocale] = useState<LocaleCode>("en");
  const [opening, setOpening] = useState(false);
  const [openErr, setOpenErr] = useState<string | null>(null);

  async function handleOpenCase() {
    setOpening(true);
    setOpenErr(null);
    try {
      const c = await openCase(alertId);
      onOpenedCase(c.case_id);
    } catch (e) {
      setOpenErr(e instanceof Error ? e.message : "Could not open case.");
    } finally {
      setOpening(false);
    }
  }

  return (
    <div className="space-y-3">
      <AsyncView state={alert.state} onRetry={alert.reload}>
        {(a) => {
          const payload = a.structured_payload as Record<string, unknown>;
          return (
            <Card
              title={alertTitle(a)}
              subtitle={`${a.alert_type} · detected ${formatDateTime(a.detected_at)}`}
              right={<SeverityBadge severity={a.severity} />}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="blue">{a.state}</Badge>
                {a.requires_case && <Badge tone="amber">requires review</Badge>}
                {a.has_case ? <Badge tone="green">case open</Badge> : <Badge tone="zinc">no case yet</Badge>}
              </div>

              {typeof payload.evidence_summary === "string" && (
                <p className="mt-3 text-sm">{payload.evidence_summary}</p>
              )}
              {typeof payload.plausible_benign_explanation === "string" && (
                <div className="mt-2 rounded bg-emerald-50 p-2 text-xs text-emerald-900 dark:bg-emerald-900/20 dark:text-emerald-200">
                  <span className="font-medium">Benign context: </span>
                  {payload.plausible_benign_explanation as string}
                </div>
              )}

              <div className="mt-3 flex items-center gap-2">
                {a.has_case && a.case_id ? (
                  <Button size="sm" onClick={() => onOpenedCase(a.case_id!)}>
                    View case
                  </Button>
                ) : canOpenCase(user) ? (
                  <Button size="sm" variant="primary" disabled={opening} onClick={handleOpenCase}>
                    {opening ? "Opening…" : "Open case"}
                  </Button>
                ) : (
                  <p className="text-xs text-zinc-500">Case creation requires an operations or risk identity.</p>
                )}
              </div>
              {openErr && <p className="mt-2 text-xs text-red-600">{openErr}</p>}
            </Card>
          );
        }}
      </AsyncView>

      <Card
        title="Explanation"
        subtitle="Immutable analytical narrative"
        right={
          <div className="flex gap-1">
            {LOCALES.map((l) => (
              <Button key={l} size="sm" variant={locale === l ? "primary" : "ghost"} onClick={() => setLocale(l)}>
                {LOCALE_LABELS[l]}
              </Button>
            ))}
          </div>
        }
      >
        <AsyncView state={explanations.state} onRetry={explanations.reload}>
          {(d) => {
            const chosen = d.explanations.find((e) => e.locale === locale) ?? d.explanations[0];
            if (!chosen) return <EmptyState>No explanation rendered for this alert.</EmptyState>;
            return <ExplanationBlock e={chosen} />;
          }}
        </AsyncView>
      </Card>
    </div>
  );
}

export default function AlertsPanel({
  outletId,
  refreshKey,
  onOpenedCase,
  user,
}: {
  outletId: string;
  refreshKey: number;
  onOpenedCase: (caseId: string) => void;
  user: Principal;
}) {
  const { state, reload } = useAsync(() => fetchAlerts(outletId), [outletId, refreshKey]);
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Alerts</h2>
        <p className="text-xs text-zinc-500">
          Published, evidence-backed alerts. Select one to read its explanation in English, বাংলা, or Banglish.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,20rem)_1fr]">
        <div>
          <AsyncView
            state={state}
            onRetry={reload}
            isEmpty={(d) => d.alerts.length === 0}
            empty={
              <EmptyState>
                No alerts yet. Publish alertable candidates from <strong>Scenarios &amp; Faults</strong> after running
                analytics.
              </EmptyState>
            }
          >
            {(d) => (
              <ul className="space-y-2">
                {d.alerts.map((a) => (
                  <li key={a.alert_id}>
                    <button
                      onClick={() => setSelected(a.alert_id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        selected === a.alert_id
                          ? "border-zinc-900 bg-zinc-50 dark:border-white dark:bg-zinc-800"
                          : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{alertTitle(a)}</span>
                        <SeverityBadge severity={a.severity} />
                      </div>
                      <p className="mt-1 text-xs text-zinc-500">
                        {a.alert_type} · {formatDateTime(a.detected_at)}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </AsyncView>
        </div>

        <div>
          {selected ? (
            <AlertDetail alertId={selected} refreshKey={refreshKey} onOpenedCase={onOpenedCase} user={user} />
          ) : (
            <EmptyState>Select an alert to view its evidence and localized explanation.</EmptyState>
          )}
        </div>
      </div>
    </div>
  );
}
