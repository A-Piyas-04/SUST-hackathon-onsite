"use client";

import Link from "next/link";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  acknowledgeCase,
  addCaseNote,
  ApiError,
  escalateCase,
  resolveCase,
  reviewCase,
  type AppRole,
  type Case,
} from "@/lib/api";
import { useCases, useCase, useCaseTimeline, queryKeys } from "@/lib/queries";
import { canPerformCaseAction, isReadOnlyCases } from "@/lib/authz";
import { useSession } from "@/lib/session";
import { CaseBadge } from "@/components/ui/CaseBadge";
import { Badge, Button, Card, EmptyState, ErrorState, Modal, Skeleton, Textarea, Select } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";

export function CasesListView() {
  const [tab, setTab] = useState<"mine" | "all">("all");
  const { data, isLoading, error, refetch } = useCases();
  const user = useSession((s) => s.user)!;

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load cases" onRetry={() => refetch()} />;

  const cases = data?.cases ?? [];
  const filtered = tab === "mine" ? cases.filter((c) => c.current_owner_user_id === user.user_id) : cases;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant={tab === "mine" ? "primary" : "default"} size="sm" onClick={() => setTab("mine")}>My queue</Button>
        <Button variant={tab === "all" ? "primary" : "default"} size="sm" onClick={() => setTab("all")}>All</Button>
      </div>
      {!filtered.length ? (
        <EmptyState>No cases</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-subtle text-left text-xs text-muted">
              <tr>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Severity</th>
                <th className="px-3 py-2">Outlet</th>
                <th className="px-3 py-2">Age</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.case_id} className="border-t border-border hover:bg-subtle">
                  <td className="px-3 py-2"><Link href={`/cases/${c.case_id}`}><CaseBadge status={c.status} /></Link></td>
                  <td className="px-3 py-2"><Badge tone="danger">high</Badge></td>
                  <td className="px-3 py-2 font-mono text-xs">{c.case_number}</td>
                  <td className="px-3 py-2 text-xs text-muted">{formatTime(c.opened_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function CaseActions({ c }: { c: Case }) {
  const user = useSession((s) => s.user)!;
  const qc = useQueryClient();
  const [modal, setModal] = useState<"ack" | "escalate" | "resolve" | "note" | null>(null);
  const [reason, setReason] = useState("");
  const [targetRole, setTargetRole] = useState<AppRole>("risk_analyst");
  const [busy, setBusy] = useState(false);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.case(c.case_id) });
    qc.invalidateQueries({ queryKey: queryKeys.caseTimeline(c.case_id) });
    setModal(null);
    setReason("");
  };

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      invalidate();
    } finally {
      setBusy(false);
    }
  }

  if (isReadOnlyCases(user)) return <p className="text-xs text-muted">Read-only</p>;

  return (
    <>
      <div className="flex flex-wrap gap-2">
        {canPerformCaseAction(user, "acknowledge") && c.status === "open" && (
          <Button size="sm" onClick={() => setModal("ack")}>Acknowledge</Button>
        )}
        {canPerformCaseAction(user, "escalate") && c.status !== "resolved" && (
          <Button size="sm" onClick={() => setModal("escalate")}>Escalate</Button>
        )}
        {canPerformCaseAction(user, "note") && (
          <Button size="sm" onClick={() => setModal("note")}>Add note</Button>
        )}
        {canPerformCaseAction(user, "resolve") && c.status !== "resolved" && (
          <Button size="sm" variant="primary" onClick={() => setModal("resolve")}>Resolve</Button>
        )}
        {canPerformCaseAction(user, "review") && (
          <Button size="sm" onClick={() => run(() => reviewCase(c.case_id, "requires_follow_up", reason || "Requires follow-up"))}>
            Requires follow-up
          </Button>
        )}
      </div>

      <Modal open={modal === "ack"} title="Acknowledge" onClose={() => setModal(null)} footer={
        <Button variant="primary" disabled={busy} onClick={() => run(() => acknowledgeCase(c.case_id, { expected_version: c.version, reason }))}>Confirm</Button>
      }>
        <Textarea value={reason} onChange={setReason} placeholder="Optional note" />
      </Modal>

      <Modal open={modal === "escalate"} title="Escalate" onClose={() => setModal(null)} footer={
        <Button variant="primary" disabled={busy || !reason.trim()} onClick={() => run(() => escalateCase(c.case_id, targetRole, { expected_version: c.version, reason }))}>Escalate</Button>
      }>
        <Select value={targetRole} onChange={(v) => setTargetRole(v as AppRole)} options={[
          { value: "risk_analyst", label: "Risk analyst" },
          { value: "area_manager", label: "Area manager" },
        ]} />
        <div className="mt-2"><Textarea value={reason} onChange={setReason} placeholder="Reason (required)" /></div>
      </Modal>

      <Modal open={modal === "resolve"} title="Resolve" onClose={() => setModal(null)} footer={
        <Button variant="primary" disabled={busy || !reason.trim()} onClick={() => run(() => resolveCase(c.case_id, reason, { expected_version: c.version }))}>Resolve</Button>
      }>
        <Textarea value={reason} onChange={setReason} placeholder="Resolution summary (required)" />
        <p className="mt-2 text-xs text-muted">No financial action taken.</p>
      </Modal>

      <Modal open={modal === "note"} title="Add note" onClose={() => setModal(null)} footer={
        <Button variant="primary" disabled={busy || !reason.trim()} onClick={() => run(() => addCaseNote(c.case_id, reason))}>Submit</Button>
      }>
        <Textarea value={reason} onChange={setReason} placeholder="Note" />
      </Modal>
    </>
  );
}

export function CaseDetailView({ caseId }: { caseId: string }) {
  const { data: c, isLoading, error, refetch } = useCase(caseId);
  const { data: timeline } = useCaseTimeline(caseId);

  if (isLoading) return <Skeleton className="h-64" />;
  if (error instanceof ApiError && error.kind === "notFound") return <EmptyState>Not found</EmptyState>;
  if (error) return <ErrorState message="Could not load case" onRetry={() => refetch()} />;
  if (!c) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <Link href="/cases" className="text-xs text-accent hover:underline">← Cases</Link>
        <h2 className="text-lg font-semibold">{c.case_number}</h2>
        <div className="mt-1 flex items-center gap-2">
          <CaseBadge status={c.status} />
          <span className="text-xs text-muted">Opened {formatTime(c.opened_at)}</span>
        </div>
      </div>

      <Card>
        <p className="text-xs font-medium text-muted">Next step</p>
        <p className="text-sm">{c.recommended_next_step}</p>
      </Card>

      {c.similar_cases && (
        <div>
          <h3 className="mb-2 text-sm font-medium">Similar past cases</h3>
          {c.similar_cases.status === "ready" && c.similar_cases.matches.length > 0 ? (
            <div className="space-y-3">
              {c.similar_cases.matches.map((m) => (
                <div key={m.case_id} className="border-l-2 border-accent/40 pl-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{m.case_number}</span>
                    <span className="font-mono text-xs text-muted">
                      {(m.similarity * 100).toFixed(0)}% similar
                    </span>
                    <span
                      className={
                        m.corpus_origin === "seeded_demo"
                          ? "text-xs text-amber-700"
                          : "text-xs text-emerald-700"
                      }
                    >
                      {m.corpus_origin === "seeded_demo" ? "Demo seed" : "Live resolution"}
                    </span>
                  </div>
                  {m.disposition && (
                    <p className="mt-1 text-xs text-muted">
                      Outcome: {m.disposition.replace(/_/g, " ")}
                      {m.was_false_positive === true ? " (false positive)" : ""}
                    </p>
                  )}
                  <p className="mt-1">{m.resolution_summary}</p>
                  {m.review_summary && (
                    <p className="mt-1 text-xs text-muted">{m.review_summary}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">
              {c.similar_cases.message ?? "No comparable cases yet"}
            </p>
          )}
        </div>
      )}

      <Link href={`/alerts/${c.alert_id}`} className="text-sm text-accent hover:underline">Source alert →</Link>

      <CaseActions c={c} />

      <div>
        <h3 className="mb-2 text-sm font-medium">Timeline</h3>
        <div className="space-y-2">
          {[...(timeline?.events ?? [])].reverse().map((e) => (
            <div key={e.event_id} className="flex gap-3 text-sm">
              <span className="w-16 shrink-0 font-mono text-xs text-muted">{formatTime(e.event_at)}</span>
              <span className="capitalize">{e.event_type.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-muted">Advisory only — no financial action.</p>
    </div>
  );
}
