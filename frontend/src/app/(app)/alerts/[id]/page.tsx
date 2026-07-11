import { AlertDetailView } from "@/components/features/alerts/AlertsView";

export default async function AlertDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AlertDetailView alertId={id} />;
}
