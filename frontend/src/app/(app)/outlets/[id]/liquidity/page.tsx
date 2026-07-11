import { LiquidityView } from "@/components/features/liquidity/LiquidityView";

export default async function LiquidityPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <LiquidityView outletId={id} />;
}
