"use client";

import type { FeedHealthStatus } from "@/lib/api";
import { cn } from "@/lib/cn";

const STATUS_CONFIG: Record<FeedHealthStatus, { tone: "success" | "warning" | "danger"; label: string }> = {
  fresh: { tone: "success", label: "Fresh" },
  stale: { tone: "warning", label: "Stale" },
  missing: { tone: "danger", label: "Missing" },
  conflicting: { tone: "danger", label: "Conflict" },
};

export function FeedStatusDot({ status, className }: { status: FeedHealthStatus; className?: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.missing;
  const dotColor =
    cfg.tone === "success" ? "bg-success" : cfg.tone === "warning" ? "bg-warning" : "bg-danger";
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs text-secondary", className)} title={cfg.label}>
      <span className={cn("h-2 w-2 rounded-full", dotColor)} />
      {cfg.label}
    </span>
  );
}

export function FeedStatusBadge({ status }: { status: FeedHealthStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.missing;
  const styles = {
    success: "bg-[var(--success-bg)] text-success border-[rgba(22,101,52,0.2)]",
    warning: "bg-[var(--warning-bg)] text-warning border-[rgba(146,64,14,0.2)]",
    danger: "bg-[var(--danger-bg)] text-danger border-[rgba(153,27,27,0.2)]",
  };
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold",
        styles[cfg.tone],
      )}
    >
      {cfg.label}
    </span>
  );
}
