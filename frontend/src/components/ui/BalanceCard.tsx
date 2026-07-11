"use client";

import type { ProviderCode } from "@/lib/api";
import { ConfidenceBar } from "./ConfidenceBar";
import { FeedStatusDot } from "./FeedStatusDot";
import { Card } from "./primitives";
import { formatDateTime, formatMoney, PROVIDER_COLORS, relativeToNow } from "@/lib/format";
import type { FeedHealthStatus } from "@/lib/api";
import Link from "next/link";

type BalanceCardProps = {
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
};

export function BalanceCard({
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
}: BalanceCardProps) {
  const stripe = provider ? PROVIDER_COLORS[provider] : "#0f766e";
  return (
    <Card stripe={stripe}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium text-secondary">{title}</span>
        {feedStatus && <FeedStatusDot status={feedStatus} />}
      </div>
      <p className={`mt-2 font-mono text-2xl font-semibold tabular-nums ${missing ? "text-muted line-through" : ""}`}>
        {missing ? "—" : formatMoney(balance, currency)}
      </p>
      <p className="mt-1 text-xs text-muted">{formatDateTime(observedAt)}</p>
      {shortageAt && (
        <p className="mt-2 text-xs text-warning">Shortage {relativeToNow(shortageAt)}</p>
      )}
      {confidenceScore && confidenceLevel && (
        <div className="mt-2">
          <ConfidenceBar score={confidenceScore} level={confidenceLevel} />
        </div>
      )}
      {projectionHref && (
        <Link href={projectionHref} className="mt-3 inline-block text-xs text-accent hover:underline">
          View projection
        </Link>
      )}
    </Card>
  );
}
