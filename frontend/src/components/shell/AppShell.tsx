"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar, DemoBanner } from "./Sidebar";
import { TopBar, HealthBanner } from "./TopBar";
import { useSession } from "@/lib/session";
import { canAccessRoute } from "@/lib/authz";
import { useDataQuality } from "@/lib/queries";
import { DEFAULT_OUTLET, lockedOutletId } from "@/lib/authz";
import { resolvePageTitle } from "@/lib/page-titles";
import { cn } from "@/lib/cn";
import { Skeleton } from "@/components/ui/primitives";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, booting, bootstrap } = useSession();
  const [collapsed, setCollapsed] = useState(false);
  const outletId = user ? (lockedOutletId(user) ?? DEFAULT_OUTLET) : DEFAULT_OUTLET;
  const { data: dq } = useDataQuality(outletId);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    if (!booting && !user) router.replace("/login");
  }, [booting, user, router]);

  useEffect(() => {
    if (user && !canAccessRoute(user, pathname)) {
      router.replace("/not-found");
    }
  }, [user, pathname, router]);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1024px)");
    const handler = () => setCollapsed(mq.matches);
    handler();
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  if (booting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-8">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }

  if (!user) return null;

  const healthIssues =
    dq?.providers
      .filter((p) => p.assessment?.status && p.assessment.status !== "fresh")
      .map((p) => ({
        provider: p.provider,
        status: p.assessment.status,
      })) ?? [];

  return (
    <div className="min-h-screen bg-background">
      <DemoBanner />
      <Sidebar collapsed={collapsed} />
      <div
        className={cn("transition-[margin]", collapsed ? "ml-[var(--sidebar-collapsed)]" : "ml-[var(--sidebar-width)]")}
      >
        <TopBar title={resolvePageTitle(pathname)} />
        <HealthBanner issues={healthIssues} />
        <main className="space-y-6 px-7 py-6">{children}</main>
      </div>
    </div>
  );
}
