import { AnomaliesListView } from "@/components/features/anomalies/AnomaliesView";

export default async function AnomaliesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AnomaliesListView outletId={id} />;
}
