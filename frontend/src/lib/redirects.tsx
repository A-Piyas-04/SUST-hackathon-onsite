"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useOutletId } from "@/lib/outlet";

export function OutletScopeRedirect({ segment }: { segment: string }) {
  const router = useRouter();
  const outletId = useOutletId();
  useEffect(() => {
    router.replace(`/outlets/${outletId}/${segment}`);
  }, [router, outletId, segment]);
  return null;
}
