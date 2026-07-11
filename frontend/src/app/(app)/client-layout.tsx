"use client";

import { AppShell } from "@/components/shell/AppShell";

export default function ClientAppShell({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
