"use client";

import { useCases, useCaseAudit } from "@/lib/queries";
import { useState } from "react";
import { Button, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";

function AuditTable({ caseId }: { caseId: string }) {
  const { data, isLoading, error } = useCaseAudit(caseId);
  if (isLoading) return <Skeleton className="h-32" />;
  if (error) return <ErrorState message="Could not load audit" />;
  if (!data?.events.length) return <EmptyState>No events</EmptyState>;

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-subtle text-left text-xs text-muted">
          <tr>
            <th className="px-3 py-2">Time</th>
            <th className="px-3 py-2">Actor</th>
            <th className="px-3 py-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {data.events.map((e) => (
            <tr key={e.audit_event_id} className="border-t border-border">
              <td className="px-3 py-2 font-mono text-xs">{formatTime(e.occurred_at)}</td>
              <td className={`px-3 py-2 text-xs ${e.actor_type === "system" ? "text-muted" : ""}`}>{e.actor_type}</td>
              <td className="px-3 py-2 capitalize">{e.action.replace(/_/g, " ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AuditView() {
  const { data: cases, isLoading } = useCases();
  const [caseId, setCaseId] = useState<string | null>(null);

  if (isLoading) return <Skeleton className="h-48" />;

  const selected = caseId ?? cases?.cases[0]?.case_id;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {cases?.cases.slice(0, 10).map((c) => (
          <Button key={c.case_id} size="sm" variant={selected === c.case_id ? "primary" : "default"} onClick={() => setCaseId(c.case_id)}>
            {c.case_number}
          </Button>
        ))}
      </div>
      {selected && (
        <>
          <Button size="sm" onClick={() => {
            const blob = new Blob([JSON.stringify({ case_id: selected })], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `audit-${selected}.json`;
            a.click();
          }}>Export JSON</Button>
          <AuditTable caseId={selected} />
        </>
      )}
    </div>
  );
}
