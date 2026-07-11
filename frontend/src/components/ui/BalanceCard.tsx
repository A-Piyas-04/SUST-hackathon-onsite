"use client";

import Link from "next/link";
import type { ProviderCode } from "@/lib/api";
import type { FeedHealthStatus } from "@/lib/api";
import { ConfidenceBar } from "./ConfidenceBar";
import { FeedStatusBadge } from "./FeedStatusDot";
import { Card } from "./primitives";
import {
  formatDateTime,
  formatMoney,
  PROVIDER_COLORS,
  providerDisplayName,
  shortageLabel,
} from "@/lib/format";

export function SharedCashCard({
  balance,
  currency = "BDT",
  observedAt,
  shortageAt,
  confidenceScore,
  confidenceLevel,
  projectionHref,
}: {
  balance: string;
  currency?: string;
  observedAt: string;
  shortageAt?: string | null;
  confidenceScore?: string;
  confidenceLevel?: string;
  projectionHref?: string;
}) {
  const hasShortage = Boolean(shortageAt);

  return (
    <Card topStripe="var(--color-cash)" className="px-6 py-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted">Shared Cash</p>
          <p className="mt-1 font-mono text-[28px] font-medium tabular-nums text-foreground">
            {formatMoney(balance, currency)}
          </p>
          <p className="mt-1 font-mono text-xs text-muted">{formatDateTime(observedAt)}</p>
        </div>
        <span
          className="inline-flex shrink-0 self-start rounded-full border px-3 py-1 text-[13px] font-semibold"
          style={
            hasShortage
              ? {
                  background: "var(--warning-bg)",
                  borderColor: "var(--warning)",
                  color: "var(--warning)",
                }
              : {
                  background: "var(--success-bg)",
                  borderColor: "var(--success)",
                  color: "var(--success)",
                }
          }
        >
          {shortageLabel(shortageAt)}
        </span>
      </div>
      {confidenceScore && confidenceLevel && (
        <div className="mt-4">
          <ConfidenceBar score={confidenceScore} level={confidenceLevel} />
        </div>
      )}
      {projectionHref && (
        <Link href={projectionHref} className="link-maroon mt-3 inline-block">
          View projection →
        </Link>
      )}
    </Card>
  );
}

export function ProviderBalanceCard({
  title,
  balance,
  currency = "BDT",
  observedAt,
  feedStatus,
  shortageAt,
  confidenceScore,
  confidenceLevel,
  provider,
  projectionHref,
  missing,
}: {
  title: string;
  balance: string;
  currency?: string;
  observedAt: string;
  feedStatus?: FeedHealthStatus;
  shortageAt?: string | null;
  confidenceScore?: string;
  confidenceLevel?: string;
  provider?: ProviderCode;
  projectionHref?: string;
  missing?: boolean;
}) {
  const stripe = provider ? PROVIDER_COLORS[provider] : undefined;
  const numericBalance = Number(balance);
  const isZeroValid = !missing && numericBalance === 0 && feedStatus === "fresh";

  return (
    <Card topStripe={stripe} className="px-5 py-5">
      <div className="flex items-start justify-between gap-2">
        <span className="text-[13px] font-semibold text-foreground">
          {provider ? providerDisplayName(provider) : title}
        </span>
        {feedStatus && <FeedStatusBadge status={feedStatus} />}
      </div>
      <p
        className={`mt-2 font-mono text-2xl font-medium tabular-nums ${
          missing ? "text-muted line-through" : isZeroValid ? "text-muted" : "text-foreground"
        }`}
        title={isZeroValid ? "Balance is 0 — feed is fresh but no transactions yet." : undefined}
      >
        {missing ? "—" : formatMoney(balance, currency)}
      </p>
      {isZeroValid && (
        <p className="mt-1 text-[11px] text-faint">Balance is 0 — feed is fresh, no transactions yet.</p>
      )}
      <p className="mt-1 font-mono text-xs text-muted">{formatDateTime(observedAt)}</p>
      {shortageAt && (
        <p className="mt-2 text-[13px] font-semibold text-warning">{shortageLabel(shortageAt)}</p>
      )}
      {confidenceScore && confidenceLevel && (
        <div className="mt-3">
          <ConfidenceBar score={confidenceScore} level={confidenceLevel} />
        </div>
      )}
      {projectionHref && (
        <Link href={projectionHref} className="link-maroon mt-3 inline-block">
          View projection →
        </Link>
      )}
    </Card>
  );
}

/** @deprecated Use SharedCashCard or ProviderBalanceCard */
export function BalanceCard(props: Parameters<typeof ProviderBalanceCard>[0] & { title: string }) {
  return <ProviderBalanceCard {...props} />;
}
