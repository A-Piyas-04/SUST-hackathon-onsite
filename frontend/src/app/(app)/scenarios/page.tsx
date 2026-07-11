"use client";

import { ScenariosView } from "@/components/features/scenarios/ScenariosView";
import { useOutletId } from "@/lib/outlet";

export default function ScenariosPage() {
  const outletId = useOutletId();
  return <ScenariosView outletId={outletId} />;
}
