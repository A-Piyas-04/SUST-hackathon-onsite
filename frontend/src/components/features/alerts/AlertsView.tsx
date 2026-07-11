"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAlerts, useAlert, useAlertExplanations } from "@/lib/queries";
import { openCase, type Alert, type LocaleCode } from "@/lib/api";
import { canOpenCase } from "@/lib/authz";
import { useSession } from "@/lib/session";
import { LocaleToggle } from "@/components/ui/LocaleToggle";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { Badge, Button, Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";
import { ApiError } from "@/lib/api";

function alertTitle(a: Alert): string {
  const map: Record<string, string> = {
    "alert.anomaly.unusual_activity": "Unusual activity",
    "alert.liquidity.shared_cash_shortage": "Liquidity pressure",
  };
  const key = a.title_key;
  if (key) return map[key] ?? key.replace(/[._]/g, " ");
  return (a.alert_type ?? "alert").replace(/_/g, " ");
}

export function AlertsListView({ outletId }: { outletId?: string }) {
  const { data, isLoading, error, refetch } = useAlerts(outletId);

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load alerts" onRetry={() => refetch()} />;
  if (!data?.alerts.length) return <EmptyState action={<Link href="/dashboard" className="text-accent">Dashboard</Link>}>No alerts</EmptyState>;

  return (
    <div className="space-y-2">
      {data.alerts.map((a) => (
        <Link key={a.alert_id} href={`/alerts/${a.alert_id}`}>
          <Card className="transition hover:bg-subtle">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <Badge tone={a.severity === "high" ? "danger" : "warning"}>{a.severity}</Badge>
                  <span className="text-xs uppercase text-muted">{a.alert_type}</span>
                  <span className="text-xs text-muted">{formatTime(a.detected_at)}</span>
                </div>
                <p className="mt-1 text-sm">{alertTitle(a)}</p>
              </div>
              <span className="text-xs text-accent">{a.has_case ? "View case →" : "View →"}</span>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}

export function AlertDetailView({ alertId }: { alertId: string }) {
  const router = useRouter();
  const user = useSession((s) => s.user)!;
  const { data: alert, isLoading, error, refetch } = useAlert(alertId);
  const { data: expl } = useAlertExplanations(alertId);
  const [locale, setLocale] = useState<LocaleCode>("en");
  const [opening, setOpening] = useState(false);

  if (isLoading) return <Skeleton className="h-64" />;
  if (error instanceof ApiError && error.kind === "notFound") {
    return <EmptyState>Not found</EmptyState>;
  }
  if (error) return <ErrorState message="Could not load alert" onRetry={() => refetch()} />;
  if (!alert) return null;

  const explanation = expl?.explanations.find((e) => e.locale === locale) ?? expl?.explanations.find((e) => e.locale === "en");
  const payload = alert.structured_payload as Record<string, unknown>;

  async function handleOpenCase() {
    setOpening(true);
    try {
      const c = await openCase(alertId);
      router.push(`/cases/${c.case_id}`);
    } finally {
      setOpening(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted">Alert {alert.alert_id.slice(0, 8)}</p>
          <h2 className="text-lg font-semibold">{alertTitle(alert)}</h2>
          <p className="text-xs text-muted">{formatTime(alert.detected_at)}</p>
        </div>
        <Badge tone={alert.severity === "high" ? "danger" : "warning"}>{alert.severity}</Badge>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-secondary">Explanation</span>
        <LocaleToggle current={locale} onChange={setLocale} />
      </div>

      {explanation && (
        <Card>
          {[
            ["Situation", explanation.situation_text],
            ["Evidence", explanation.evidence_text],
            ["Uncertainty", explanation.uncertainty_text],
            ["Next step", explanation.next_step_text],
          ].map(([label, text]) => (
            <div key={label} className="mb-3 last:mb-0">
              <p className="text-xs font-medium text-muted">{label}</p>
              <p className="text-sm">{text}</p>
            </div>
          ))}
        </Card>
      )}

      {typeof payload.confidence_score === "string" && (
        <ConfidenceBar score={payload.confidence_score as string} level={(payload.confidence_level as string) ?? "medium"} />
      )}

      <div className="flex gap-2">
        {alert.has_case && alert.case_id ? (
          <Button onClick={() => router.push(`/cases/${alert.case_id}`)}>View case</Button>
        ) : canOpenCase(user) ? (
          <Button variant="primary" disabled={opening} onClick={handleOpenCase}>Open case</Button>
        ) : null}
      </div>
    </div>
  );
}
