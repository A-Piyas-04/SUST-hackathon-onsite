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
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function relativeToNow(value: string | null | undefined): string {
  if (!value) return "—";
  const diffMs = new Date(value).getTime() - Date.now();
  const abs = Math.abs(diffMs);
  const mins = Math.round(abs / 60000);
  if (mins < 60) return diffMs >= 0 ? `~${mins}m` : `${mins}m ago`;
  const hrs = Math.round(abs / 3600000);
  if (hrs < 48) return diffMs >= 0 ? `~${hrs}h` : `${hrs}h ago`;
  const days = Math.round(abs / 86400000);
  return diffMs >= 0 ? `~${days}d` : `${days}d ago`;
}

export function secondsAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  return `${Math.round(s / 60)}m ago`;
}

export function confidencePct(score: string | number): number {
  return Math.round(Number(score) * 100);
}

export const PROVIDER_COLORS: Record<string, string> = {
  bkash: "var(--color-bkash)",
  nagad: "var(--color-nagad)",
  rocket: "var(--color-rocket)",
};

export const LOCALE_LABELS: Record<string, string> = {
  en: "EN",
  bn: "বাং",
  bn_latn: "BNG",
};
