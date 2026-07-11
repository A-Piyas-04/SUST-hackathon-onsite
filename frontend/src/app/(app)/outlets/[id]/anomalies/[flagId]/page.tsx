import { AnomalyDetailView } from "@/components/features/anomalies/AnomaliesView";

export default async function AnomalyDetailPage({
  params,
}: {
  params: Promise<{ id: string; flagId: string }>;
}) {
  const { id, flagId } = await params;
  return <AnomalyDetailView outletId={id} flagId={flagId} />;
}
