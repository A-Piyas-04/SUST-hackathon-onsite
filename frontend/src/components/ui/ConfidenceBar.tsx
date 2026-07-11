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
  const fill =
    pct >= 75 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-danger";

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="mb-1 flex items-center justify-between text-[11px] text-muted">
          <span>Confidence</span>
          <span className="tabular-nums">{pct}%</span>
        </div>
      )}
      <div className="h-1 overflow-hidden rounded-sm bg-surface-raised">
        <div className={cn("h-full rounded-sm transition-all", fill)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
