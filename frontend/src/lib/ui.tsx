"use client";

/**
 * Thin shared UI primitives for the demo shell. Deliberately minimal — clarity
 * over polish. Includes the four mandated data states (loading / empty / error /
 * forbidden) with forbidden rendered identically to not-found so the existence of
 * cross-provider confidential records is never revealed.
 */

import { ReactNode } from "react";
import { ApiError } from "./api";

// --------------------------------------------------------------------------- //
// Formatting
// --------------------------------------------------------------------------- //
export function formatMoney(value: string | number, currency = "BDT"): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(n)) return `${value}`;
  return `${currency} ${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function relativeToNow(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value).getTime();
  const diffMs = d - Date.now();
  const abs = Math.abs(diffMs);
  const mins = Math.round(abs / 60000);
  if (mins < 60) return diffMs >= 0 ? `in ~${mins} min` : `${mins} min ago`;
  const hrs = Math.round(abs / 3600000);
  if (hrs < 48) return diffMs >= 0 ? `in ~${hrs} h` : `${hrs} h ago`;
  const days = Math.round(abs / 86400000);
  return diffMs >= 0 ? `in ~${days} d` : `${days} d ago`;
}

// --------------------------------------------------------------------------- //
// Layout primitives
// --------------------------------------------------------------------------- //
export function Card({
  title,
  subtitle,
  children,
  right,
  accent,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  right?: ReactNode;
  accent?: string;
}) {
  return (
    <section
      className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
      style={accent ? { borderTopWidth: 3, borderTopColor: accent } : undefined}
    >
      {(title || right) && (
        <header className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="text-sm font-semibold">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-zinc-500">{subtitle}</p>}
          </div>
          {right}
        </header>
      )}
      {children}
    </section>
  );
}

// --------------------------------------------------------------------------- //
// Badges
// --------------------------------------------------------------------------- //
export function Badge({ children, tone = "zinc" }: { children: ReactNode; tone?: BadgeTone }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${TONE[tone]}`}>{children}</span>;
}

export type BadgeTone = "zinc" | "green" | "amber" | "red" | "blue" | "violet" | "slate";
const TONE: Record<BadgeTone, string> = {
  zinc: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  green: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  amber: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  red: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  blue: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  violet: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300",
  slate: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
};

export function ConfidenceBadge({ level, score }: { level: string; score?: string | number }) {
  const tone: BadgeTone =
    level === "high" ? "green" : level === "medium" ? "amber" : level === "low" ? "red" : "slate";
  const pct = score !== undefined ? ` · ${Math.round(Number(score) * 100)}%` : "";
  return (
    <Badge tone={tone}>
      Confidence: {level}
      {pct}
    </Badge>
  );
}

export function FeedHealthBadge({ status }: { status: string }) {
  const tone: BadgeTone =
    status === "fresh" ? "green" : status === "stale" ? "amber" : status === "conflicting" ? "red" : "slate";
  return <Badge tone={tone}>Feed: {status}</Badge>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const tone: BadgeTone =
    severity === "critical" || severity === "high" ? "red" : severity === "medium" ? "amber" : "blue";
  return <Badge tone={tone}>{severity}</Badge>;
}

export function DispositionBadge({ disposition }: { disposition: string }) {
  if (disposition === "suppressed_data_quality")
    return <Badge tone="slate">suppressed · not alertable</Badge>;
  if (disposition === "requires_review") return <Badge tone="amber">requires review</Badge>;
  if (disposition === "dismissed_benign") return <Badge tone="green">benign</Badge>;
  return <Badge tone="zinc">{disposition.replace(/_/g, " ")}</Badge>;
}

export function CaseStatusBadge({ status }: { status: string }) {
  const tone: BadgeTone =
    status === "resolved" ? "green" : status === "escalated" ? "red" : status === "acknowledged" ? "blue" : "amber";
  return <Badge tone={tone}>{status}</Badge>;
}

// --------------------------------------------------------------------------- //
// Buttons
// --------------------------------------------------------------------------- //
export function Button({
  children,
  onClick,
  disabled,
  variant = "default",
  size = "md",
  type = "button",
  title,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "primary" | "ghost";
  size?: "sm" | "md";
  type?: "button" | "submit";
  title?: string;
}) {
  const base =
    "inline-flex items-center justify-center rounded-md font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
  const sizing = size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const styles =
    variant === "primary"
      ? "bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
      : variant === "ghost"
        ? "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
        : "border border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:bg-zinc-800";
  return (
    <button type={type} title={title} onClick={onClick} disabled={disabled} className={`${base} ${sizing} ${styles}`}>
      {children}
    </button>
  );
}

// --------------------------------------------------------------------------- //
// The four mandated data states
// --------------------------------------------------------------------------- //
export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-6 text-sm text-zinc-500">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600" />
      {label}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 py-6 text-center text-sm text-zinc-500 dark:border-zinc-700">
      {children}
    </div>
  );
}

/**
 * Error/forbidden renderer. Forbidden (safe not-found, 404 on a confidential
 * resource) is presented exactly like a benign "not found" — no "access denied"
 * wording that would reveal a cross-provider record exists (guardrail 7).
 */
export function ErrorState({ error, onRetry }: { error: ApiError | Error; onRetry?: () => void }) {
  const api = error instanceof ApiError ? error : null;
  const isNotFound = api?.kind === "notFound";
  const tone = isNotFound ? "text-zinc-600" : "text-red-700 dark:text-red-300";
  const message = isNotFound
    ? "Not available. This record does not exist, or is outside your access scope."
    : api?.message ?? error.message;
  return (
    <div className={`rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm dark:border-zinc-800 dark:bg-zinc-900 ${tone}`}>
      <p>{message}</p>
      {onRetry && !isNotFound && (
        <div className="mt-2">
          <Button size="sm" onClick={onRetry}>
            Retry
          </Button>
        </div>
      )}
    </div>
  );
}

/** Discriminated async state used across every data-fetching surface. */
export type Async<T> =
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "error"; error: ApiError | Error };

export function AsyncView<T>({
  state,
  onRetry,
  empty,
  isEmpty,
  children,
}: {
  state: Async<T>;
  onRetry?: () => void;
  empty?: ReactNode;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => ReactNode;
}) {
  if (state.kind === "loading") return <Spinner />;
  if (state.kind === "error") return <ErrorState error={state.error} onRetry={onRetry} />;
  if (empty && isEmpty && isEmpty(state.data)) return <>{empty}</>;
  return <>{children(state.data)}</>;
}

export const LOCALE_LABELS: Record<string, string> = {
  en: "English",
  bn: "বাংলা",
  bn_latn: "Banglish",
};
