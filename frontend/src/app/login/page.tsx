"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DEMO_USERS, demoLogin, setToken, ApiError } from "@/lib/api";
import { useSession } from "@/lib/session";
import { Button, Card, ErrorState } from "@/components/ui/primitives";

export default function LoginPage() {
  const router = useRouter();
  const { user, booting, bootstrap, setUser } = useSession();
  const [selected, setSelected] = useState(DEMO_USERS[0]?.key ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    if (!booting && user) router.replace("/dashboard");
  }, [booting, user, router]);

  if (booting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-muted">Loading…</p>
      </div>
    );
  }

  if (user) return null;

  async function enter() {
    setBusy(true);
    setError(null);
    try {
      const res = await demoLogin(selected);
      setToken(res.token);
      setUser(res.user);
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="mb-8 text-center">
        <h1 className="text-xl font-semibold">Liquidity Platform</h1>
        <p className="mt-1 text-sm text-muted">bKash · Nagad · Rocket</p>
      </div>
      <Card className="w-full max-w-lg">
        <p className="mb-4 text-sm font-medium">Select role</p>
        <div className="space-y-2">
          {DEMO_USERS.map((u) => (
            <label
              key={u.key}
              className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 transition ${
                selected === u.key ? "border-accent bg-accent/5" : "border-border hover:bg-subtle"
              }`}
            >
              <input
                type="radio"
                name="role"
                checked={selected === u.key}
                onChange={() => setSelected(u.key)}
                className="mt-1"
              />
              <div>
                <p className="text-sm font-medium">{u.label}</p>
                <p className="text-xs text-muted">{u.note}</p>
              </div>
            </label>
          ))}
        </div>
        <Button variant="primary" className="mt-4 w-full" disabled={busy} onClick={enter}>
          Enter
        </Button>
        {error && <div className="mt-3"><ErrorState message={error} /></div>}
      </Card>
      <p className="mt-4 text-xs text-muted">Demo · Synthetic data</p>
    </div>
  );
}
