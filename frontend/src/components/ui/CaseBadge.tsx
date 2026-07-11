"use client";

import type { CaseStatus } from "@/lib/api";
import { cn } from "@/lib/cn";

const STATUS_DOT: Record<CaseStatus, string> = {
  open: "bg-warning",
  acknowledged: "bg-info",
  escalated: "bg-[var(--color-rocket)]",
  resolved: "bg-success",
};

export function CaseBadge({ status }: { status: CaseStatus | string }) {
  const dot = STATUS_DOT[status as CaseStatus] ?? "bg-muted";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs capitalize">
      <span className={cn("h-2 w-2 rounded-full", dot)} />
      {status.replace(/_/g, " ")}
    </span>
  );
}
