"use client";

import { Area, AreaChart, Line, ResponsiveContainer, XAxis, YAxis } from "recharts";

export function ConfidenceConeChart({
  balance,
  shortageAt,
  confidence,
}: {
  balance: number;
  shortageAt: string | null;
  confidence: number;
  lowerBound?: string | null;
  upperBound?: string | null;
}) {
  const now = Date.now();
  const points = Array.from({ length: 12 }, (_, i) => {
    const t = now + i * 15 * 60_000;
    const drift = balance - (i * balance * 0.02);
    const spread = balance * (1 - confidence) * (i / 6);
    return {
      t: new Date(t).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }),
      balance: Math.max(0, drift),
      upper: Math.max(0, drift + spread),
      lower: Math.max(0, drift - spread),
    };
  });

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="mb-2 text-sm font-medium">Projection</p>
      {shortageAt && (
        <p className="mb-2 text-xs text-warning">Shortage projected</p>
      )}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={points}>
            <XAxis dataKey="t" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} width={50} />
            <Area type="monotone" dataKey="upper" stroke="none" fill="var(--color-warning)" fillOpacity={0.15} />
            <Area type="monotone" dataKey="lower" stroke="none" fill="var(--color-bg-base)" fillOpacity={1} />
            <Line type="monotone" dataKey="balance" stroke="var(--color-accent)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
