import { DashboardView } from "@/components/features/dashboard/DashboardView";

export default async function OutletDashboardPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DashboardView outletId={id} />;
}
