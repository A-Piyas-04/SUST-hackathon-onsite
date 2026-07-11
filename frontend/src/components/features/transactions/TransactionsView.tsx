"use client";

import { useState } from "react";
import { useTransactions } from "@/lib/queries";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Button, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { formatMoney, formatTime } from "@/lib/format";

export function TransactionsView({ outletId }: { outletId: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useTransactions(outletId, { page, page_size: 20 });

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;

  const total = data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / 20));
  const rows = data?.transactions ?? [];

  function exportCsv() {
    const header = "time,type,provider,amount,party,status\n";
    const body = rows.map((t) =>
      [t.occurred_at, t.transaction_type, t.provider, t.amount, t.synthetic_party_ref, t.status].join(","),
    ).join("\n");
    const blob = new Blob([header + body], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transactions.csv";
    a.click();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">{total} transactions</p>
        <Button size="sm" onClick={exportCsv}>Export</Button>
      </div>
      {!rows.length ? (
        <EmptyState>No transactions</EmptyState>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-subtle text-left text-xs text-muted">
                <tr>
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Provider</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Party</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.transaction_id} className="border-t border-border">
                    <td className="px-3 py-2 font-mono text-xs">{formatTime(t.occurred_at)}</td>
                    <td className="px-3 py-2 capitalize">{(t.transaction_type ?? "—").replace(/_/g, " ")}</td>
                    <td className="px-3 py-2"><ProviderChip provider={t.provider} /></td>
                    <td className="px-3 py-2 font-mono">{formatMoney(t.amount, t.currency_code)}</td>
                    <td className="px-3 py-2 font-mono text-xs">{t.synthetic_party_ref}</td>
                    <td className="px-3 py-2 capitalize">{t.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between text-xs text-muted">
            <span>Page {page} / {pages}</span>
            <div className="flex gap-2">
              <Button size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
              <Button size="sm" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next</Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
