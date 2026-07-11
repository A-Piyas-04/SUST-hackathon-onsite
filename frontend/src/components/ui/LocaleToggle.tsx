"use client";

import type { LocaleCode } from "@/lib/api";
import { LOCALE_LABELS } from "@/lib/format";
import { cn } from "@/lib/cn";

export function LocaleToggle({
  current,
  onChange,
}: {
  current: LocaleCode;
  onChange: (locale: LocaleCode) => void;
}) {
  const locales: LocaleCode[] = ["en", "bn", "bn_latn"];
  return (
    <div className="inline-flex rounded-md border border-border bg-elevated p-0.5">
      {locales.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => onChange(l)}
          className={cn(
            "rounded px-2 py-0.5 text-xs transition",
            current === l ? "bg-accent text-white" : "text-secondary hover:text-foreground",
          )}
        >
          {LOCALE_LABELS[l]}
        </button>
      ))}
    </div>
  );
}
