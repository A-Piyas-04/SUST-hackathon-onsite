import { TransactionsView } from "@/components/features/transactions/TransactionsView";

export default async function TransactionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TransactionsView outletId={id} />;
}
