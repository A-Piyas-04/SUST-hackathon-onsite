import { DataQualityView } from "@/components/features/data-quality/DataQualityView";

export default async function DataQualityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DataQualityView outletId={id} />;
}
