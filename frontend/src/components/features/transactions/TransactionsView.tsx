"use client";

import { useState } from "react";
import { useTransactions } from "@/lib/queries";
import { ProviderChip } from "@/components/ui/ProviderChip";
import { Button, EmptyState, ErrorState, FilterChip, Skeleton } from "@/components/ui/primitives";
import { formatMoney, formatTime } from "@/lib/format";
import type { ProviderCode, TransactionType } from "@/lib/api";

function StatusCell({ status }: { status: string }) {
  const tone =
    status === "completed" ? "text-success" : status === "pending" ? "text-warning" : "text-danger";
  return (
    <span className={`inline-flex items-center gap-1.5 capitalize ${tone}`}>
      <span className="text-[8px]">●</span>
      {status}
    </span>
  );
}

export function TransactionsView({ outletId }: { outletId: string }) {
  const [page, setPage] = useState(1);
  const [provider, setProvider] = useState<ProviderCode | "all">("all");
  const [txType, setTxType] = useState<TransactionType | "all">("all");

  const { data, isLoading, error, refetch } = useTransactions(outletId, {
    page,
    page_size: 20,
    provider_code: provider === "all" ? undefined : provider,
    transaction_type: txType === "all" ? undefined : txType,
  });

  if (isLoading) return <Skeleton className="h-48" />;
  if (error) return <ErrorState message="Could not load" onRetry={() => refetch()} />;

  const total = data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / 20));
  const rows = data?.transactions ?? [];

  function exportCsv() {
    const header = "time,type,provider,amount,party,status\n";
    const body = rows
      .map((t) =>
        [t.occurred_at, t.transaction_type, t.provider, t.amount, t.synthetic_party_ref, t.status].join(","),
      )
      .join("\n");
    const blob = new Blob([header + body], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transactions.csv";
    a.click();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-2 text-xs font-medium text-muted">Provider</span>
        {(["all", "bkash", "nagad", "rocket"] as const).map((p) => (
          <FilterChip
            key={p}
            active={provider === p}
            onClick={() => {
              setProvider(p);
              setPage(1);
            }}
          >
            {p === "all" ? "All" : p === "bkash" ? "bKash" : p.charAt(0).toUpperCase() + p.slice(1)}
          </FilterChip>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-2 text-xs font-medium text-muted">Type</span>
        {(["all", "cash_in", "cash_out"] as const).map((t) => (
          <FilterChip
            key={t}
            active={txType === t}
            onClick={() => {
              setTxType(t);
              setPage(1);
            }}
          >
            {t === "all" ? "All" : t === "cash_in" ? "Cash In" : "Cash Out"}
          </FilterChip>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">{total} transactions</p>
        <Button size="sm" variant="primary" onClick={exportCsv}>
          Export
        </Button>
      </div>

      {!rows.length ? (
        <EmptyState>No transactions</EmptyState>
      ) : (
        <>
          <div className="overflow-x-auto rounded-[12px] border border-border">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Provider</th>
                  <th className="text-right">Amount</th>
                  <th>Party</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.transaction_id}>
                    <td className="font-mono text-xs text-muted">{formatTime(t.occurred_at)}</td>
                    <td className="capitalize">{(t.transaction_type ?? "—").replace(/_/g, " ")}</td>
                    <td>
                      <ProviderChip provider={t.provider} />
                    </td>
                    <td className="text-right font-mono">{formatMoney(t.amount, t.currency_code)}</td>
                    <td className="font-mono text-[13px] text-[var(--text-faint)]">{t.synthetic_party_ref}</td>
                    <td>
                      <StatusCell status={t.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              Page {page} / {pages}
            </span>
            <div className="flex gap-2">
              <Button size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </Button>
              <Button size="sm" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
