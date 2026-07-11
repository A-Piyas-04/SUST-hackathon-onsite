"use client";

import type { ProviderCode } from "@/lib/api";
import { providerDisplayName } from "@/lib/format";
import { cn } from "@/lib/cn";

const CHIP_STYLES: Record<string, { bg: string; color: string }> = {
  bkash: { bg: "rgba(176, 16, 88, 0.08)", color: "var(--color-bkash)" },
  nagad: { bg: "rgba(200, 74, 16, 0.08)", color: "var(--color-nagad)" },
  rocket: { bg: "rgba(107, 37, 120, 0.08)", color: "var(--color-rocket)" },
};

export function ProviderChip({ provider, className }: { provider: ProviderCode | string; className?: string }) {
  const key = provider.toLowerCase();
  const style = CHIP_STYLES[key] ?? { bg: "var(--surface-raised)", color: "var(--text-body)" };
  return (
    <span
      className={cn("inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold", className)}
      style={{ backgroundColor: style.bg, color: style.color }}
    >
      {providerDisplayName(key)}
    </span>
  );
}
