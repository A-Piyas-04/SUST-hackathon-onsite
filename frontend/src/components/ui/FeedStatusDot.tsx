"use client";

import type { FeedHealthStatus } from "@/lib/api";
import { cn } from "@/lib/cn";

const STATUS_CONFIG: Record<FeedHealthStatus, { color: string; label: string }> = {
  fresh: { color: "bg-success", label: "Fresh" },
  stale: { color: "bg-warning", label: "Stale" },
  missing: { color: "bg-danger", label: "Missing" },
  conflicting: { color: "bg-danger", label: "Conflict" },
};

export function FeedStatusDot({ status, className }: { status: FeedHealthStatus; className?: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.missing;
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs text-secondary", className)} title={cfg.label}>
      <span className={cn("h-2 w-2 rounded-full", cfg.color)} />
      {cfg.label}
    </span>
  );
}

export function FeedStatusBadge({ status }: { status: FeedHealthStatus }) {
  return <FeedStatusDot status={status} />;
}
