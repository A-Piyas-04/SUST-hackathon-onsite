"use client";

import type { ProviderCode } from "@/lib/api";
import { PROVIDER_COLORS } from "@/lib/format";
import { cn } from "@/lib/cn";

export function ProviderChip({ provider, className }: { provider: ProviderCode | string; className?: string }) {
  const color = PROVIDER_COLORS[provider] ?? "var(--color-text-secondary)";
  return (
    <span
      className={cn("inline-flex rounded px-1.5 py-0.5 text-xs font-medium", className)}
      style={{ backgroundColor: `${color}18`, color }}
    >
      {provider}
    </span>
  );
}
