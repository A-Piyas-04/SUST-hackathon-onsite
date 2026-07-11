"use client";

import { secondsAgo } from "@/lib/format";
import { cn } from "@/lib/cn";

export function LastUpdated({
  generatedAt,
  onRefresh,
  className,
}: {
  generatedAt: string | null | undefined;
  onRefresh?: () => void;
  className?: string;
}) {
  if (!generatedAt) return null;
  return (
    <button
      type="button"
      onClick={onRefresh}
      className={cn("text-xs text-muted hover:text-secondary", className)}
      title="Refresh"
    >
      {secondsAgo(generatedAt)}
    </button>
  );
}
