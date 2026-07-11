"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/session";
import { DEFAULT_OUTLET, lockedOutletId } from "@/lib/authz";

export function useOutletId(): string {
  const user = useSession((s) => s.user);
  return lockedOutletId(user!) ?? DEFAULT_OUTLET;
}

export function OutletRedirect() {
  const router = useRouter();
  const outletId = useOutletId();
  useEffect(() => {
    router.replace(`/outlets/${outletId}`);
  }, [router, outletId]);
  return null;
}
