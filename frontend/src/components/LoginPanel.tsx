"use client";

import { useState } from "react";
import { ApiError, DEMO_USERS, demoLogin, Principal, setToken } from "@/lib/api";
import { Card } from "@/lib/ui";

export default function LoginPanel({ onLogin }: { onLogin: (p: Principal) => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function login(userKey: string) {
    setBusy(userKey);
    setError(null);
    try {
      const res = await demoLogin(userKey);
      setToken(res.token);
      onLogin(res.user);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Login failed. Is the backend running?");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-2xl py-10">
      <h1 className="text-xl font-semibold">Multi-Provider Agent Liquidity &amp; Coordination Platform</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Decision-support demo. Sign in as a representative role to explore its scope. Identities and data are synthetic.
      </p>

      <Card title="Demo login / role switch" subtitle="Choose a seeded identity">
        <ul className="grid gap-2 sm:grid-cols-2">
          {DEMO_USERS.map((u) => (
            <li key={u.key}>
              <button
                onClick={() => login(u.key)}
                disabled={busy !== null}
                className="w-full rounded-lg border border-zinc-200 p-3 text-left transition hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
              >
                <span className="text-sm font-medium">{u.label}</span>
                <span className="mt-0.5 block text-xs text-zinc-500">
                  {u.role.replace(/_/g, " ")} · {u.note}
                </span>
                {busy === u.key && <span className="mt-1 block text-xs text-zinc-400">Signing in…</span>}
              </button>
            </li>
          ))}
        </ul>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>
    </div>
  );
}
