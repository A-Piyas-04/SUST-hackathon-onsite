"use client";

import { useState } from "react";
import {
  acknowledgeCase,
  addCaseNote,
  ApiError,
  Case,
  escalateCase,
  fetchCase,
  fetchCaseAudit,
  fetchCases,
  fetchCaseTimeline,
  Principal,
  resolveCase,
  reviewCase,
} from "@/lib/api";
import { canPerformCaseAction, isReadOnlyCases } from "@/lib/authz";
import { useAsync } from "@/lib/hooks";
import {
  AsyncView,
  Badge,
  Button,
  Card,
  CaseStatusBadge,
  EmptyState,
  formatDateTime,
} from "@/lib/ui";

function CaseActions({
  c,
  user,
  onChanged,
}: {
  c: Case;
  user: Principal;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<{ text: string; err: boolean } | null>(null);

  async function guard(key: string, fn: () => Promise<void>) {
    setBusy(key);
    setMsg(null);
    try {
      await fn();
      onChanged();
    } catch (e) {
      const text = e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Action failed.";
      setMsg({ text, err: true });
    } finally {
      setBusy(null);
    }
  }

  const resolved = c.status === "resolved";
  const readOnly = isReadOnlyCases(user);

  if (readOnly) {
    return (
      <p className="text-xs text-zinc-500">
        Read-only case summary for your role. Operational actions require an assigned operations identity.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {canPerformCaseAction(user, "acknowledge") && (
        <Button
          size="sm"
          disabled={resolved || c.status !== "open" || busy !== null}
          onClick={() => guard("ack", () => acknowledgeCase(c.case_id, { expected_version: c.version }).then(() => {}))}
        >
          Acknowledge
        </Button>
        )}
        {canPerformCaseAction(user, "escalate") && (
        <Button
          size="sm"
          disabled={resolved || busy !== null}
          onClick={() =>
            guard("esc", () =>
              escalateCase(c.case_id, "risk_analyst", { expected_version: c.version }).then(() => {}),
            )
          }
        >
          Escalate → risk analyst
        </Button>
        )}
        {canPerformCaseAction(user, "review") && (
        <Button
          size="sm"
          disabled={resolved || busy !== null}
          onClick={() =>
            guard("review", () =>
              reviewCase(
                c.case_id,
                "requires_follow_up",
                "Pattern reviewed; benign operational context plausible, monitoring continues.",
              ).then(() => {}),
            )
          }
        >
          Add review
        </Button>
        )}
        {canPerformCaseAction(user, "resolve") && (
        <Button
          size="sm"
          variant="primary"
          disabled={resolved || busy !== null}
          onClick={() =>
            guard("resolve", () =>
              resolveCase(c.case_id, "Reviewed and coordinated; no further action required at this time.", {
                expected_version: c.version,
              }).then(() => {}),
            )
          }
        >
          Resolve
        </Button>
        )}
      </div>

      {canPerformCaseAction(user, "note") && (
      <div className="flex items-center gap-2">
        <input
          className="flex-1 rounded border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          placeholder="Add a case note…"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          disabled={resolved}
        />
        <Button
          size="sm"
          disabled={resolved || busy !== null || note.trim().length === 0}
          onClick={() => guard("note", () => addCaseNote(c.case_id, note.trim(), "general").then(() => setNote("")))}
        >
          Add note
        </Button>
      </div>
      )}

      {msg && <p className={`text-xs ${msg.err ? "text-red-600" : "text-emerald-600"}`}>{msg.text}</p>}
      <p className="text-xs text-zinc-400">
        Mutations use the case version for optimistic concurrency; stale versions fail safely. Alert evidence is never
        modified by these actions.
      </p>
    </div>
  );
}

function TimelineView({ caseId, refreshKey }: { caseId: string; refreshKey: number }) {
  const { state, reload } = useAsync(() => fetchCaseTimeline(caseId), [caseId, refreshKey]);
  return (
    <AsyncView state={state} onRetry={reload}>
      {(d) => (
        <ol className="space-y-1">
          {d.events.map((e) => (
            <li key={e.event_id} className="flex items-baseline gap-2 text-xs">
              <span className="w-32 shrink-0 text-zinc-400">{formatDateTime(e.event_at)}</span>
              <Badge tone="slate">{e.event_type.replace(/_/g, " ")}</Badge>
            </li>
          ))}
        </ol>
      )}
    </AsyncView>
  );
}

function AuditView({ caseId, refreshKey }: { caseId: string; refreshKey: number }) {
  const { state, reload } = useAsync(() => fetchCaseAudit(caseId), [caseId, refreshKey]);
  return (
    <AsyncView state={state} onRetry={reload}>
      {(d) => (
        <ol className="space-y-1">
          {d.events.map((e) => (
            <li key={e.audit_event_id} className="flex items-baseline gap-2 text-xs">
              <span className="w-32 shrink-0 text-zinc-400">{formatDateTime(e.occurred_at)}</span>
              <Badge tone="zinc">{e.action.replace(/_/g, " ")}</Badge>
              <span className="text-zinc-500">{e.actor_type}</span>
            </li>
          ))}
        </ol>
      )}
    </AsyncView>
  );
}

function CaseDetail({ caseId, user }: { caseId: string; user: Principal }) {
  const [localKey, setLocalKey] = useState(0);
  const { state, reload } = useAsync(() => fetchCase(caseId), [caseId, localKey]);
  const changed = () => setLocalKey((k) => k + 1);

  return (
    <AsyncView state={state} onRetry={reload}>
      {(c) => (
        <div className="space-y-3">
          <Card
            title={`Case ${c.case_number}`}
            subtitle={`Opened ${formatDateTime(c.opened_at)} · v${c.version}`}
            right={<CaseStatusBadge status={c.status} />}
          >
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <dt className="text-xs text-zinc-500">Current owner</dt>
                <dd>{c.current_owner_role.replace(/_/g, " ")}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Status</dt>
                <dd>{c.status}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-xs text-zinc-500">Recommended next step</dt>
                <dd>{c.recommended_next_step}</dd>
              </div>
              {c.resolution_summary && (
                <div className="col-span-2">
                  <dt className="text-xs text-zinc-500">Resolution</dt>
                  <dd>{c.resolution_summary}</dd>
                </div>
              )}
            </dl>
            <div className="mt-4">
              <CaseActions c={c} user={user} onChanged={changed} />
            </div>
          </Card>

          <div className="grid gap-3 md:grid-cols-2">
            <Card title="Timeline" subtitle="Ordered case + evidence events">
              <TimelineView caseId={caseId} refreshKey={localKey} />
            </Card>
            <Card title="Audit trail" subtitle="Immutable, ordered audit events">
              <AuditView caseId={caseId} refreshKey={localKey} />
            </Card>
          </div>
        </div>
      )}
    </AsyncView>
  );
}

export default function CasePanel({
  refreshKey,
  selectedCaseId,
  onSelect,
  user,
}: {
  refreshKey: number;
  selectedCaseId: string | null;
  onSelect: (id: string) => void;
  user: Principal;
}) {
  const { state, reload } = useAsync(() => fetchCases(), [refreshKey]);
  // Selection is fully controlled by the parent so opening a case from an alert
  // (which navigates to this tab) and clicking a row share one source of truth.
  const selected = selectedCaseId;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Case workflow</h2>
        <p className="text-xs text-zinc-500">
          Coordinate the response: acknowledge, note, escalate, review, resolve — with owner, next step, and status
          always visible.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,20rem)_1fr]">
        <div>
          <AsyncView
            state={state}
            onRetry={reload}
            isEmpty={(d) => d.cases.length === 0}
            empty={<EmptyState>No cases yet. Open one from an alert in the Alerts tab.</EmptyState>}
          >
            {(d) => (
              <ul className="space-y-2">
                {d.cases.map((c) => (
                  <li key={c.case_id}>
                    <button
                      onClick={() => onSelect(c.case_id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        selected === c.case_id
                          ? "border-zinc-900 bg-zinc-50 dark:border-white dark:bg-zinc-800"
                          : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{c.case_number}</span>
                        <CaseStatusBadge status={c.status} />
                      </div>
                      <p className="mt-1 text-xs text-zinc-500">Owner: {c.current_owner_role.replace(/_/g, " ")}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </AsyncView>
        </div>

        <div>
          {selected ? <CaseDetail caseId={selected} user={user} /> : <EmptyState>Select a case to manage its lifecycle.</EmptyState>}
        </div>
      </div>
    </div>
  );
}
