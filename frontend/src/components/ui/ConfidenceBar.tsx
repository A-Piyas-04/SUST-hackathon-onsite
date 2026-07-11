"use client";

import { confidencePct } from "@/lib/format";
import { cn } from "@/lib/cn";

export function ConfidenceBar({
  score,
  level,
  showLabel = true,
  className,
}: {
  score: string | number;
  level: string;
  showLabel?: boolean;
  className?: string;
}) {
  const pct = confidencePct(score);
  const color =
    level === "high" ? "bg-success" : level === "medium" ? "bg-warning" : level === "low" ? "bg-danger" : "bg-muted";
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-subtle">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && <span className="text-xs text-secondary tabular-nums">{pct}%</span>}
    </div>
  );
}
