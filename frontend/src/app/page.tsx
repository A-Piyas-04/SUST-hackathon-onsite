import { fetchHealth, getApiBaseUrl } from "@/lib/api";

type HealthState =
  | { kind: "loading" }
  | { kind: "ready"; status: string; dbReady: boolean }
  | { kind: "error"; message: string };

async function loadHealth(): Promise<HealthState> {
  try {
    const health = await fetchHealth();
    return {
      kind: "ready",
      status: health.status,
      dbReady: health.database.ready,
    };
  } catch (error) {
    return {
      kind: "error",
      message: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

export default async function Home() {
  const apiBaseUrl = getApiBaseUrl();
  const health = await loadHealth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-6 font-sans text-zinc-900">
      <main className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Phase 2 shell
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          Multi-Provider Agent Liquidity Platform
        </h1>
        <p className="mt-3 text-sm leading-6 text-zinc-600">
          Thin frontend scaffold for the hackathon prototype. Feature UI arrives in
          Phase 6; this page only verifies backend connectivity.
        </p>

        <dl className="mt-6 space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-zinc-500">Backend base URL</dt>
            <dd className="font-mono text-xs">{apiBaseUrl}</dd>
          </div>
          <div className="flex items-center justify-between gap-4">
            <dt className="text-zinc-500">Health status</dt>
            <dd>
              {health.kind === "loading" && (
                <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs">Loading…</span>
              )}
              {health.kind === "ready" && (
                <span
                  className={`rounded-full px-3 py-1 text-xs ${
                    health.dbReady
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {health.status}
                  {health.dbReady ? " · DB ready" : " · DB not ready"}
                </span>
              )}
              {health.kind === "error" && (
                <span className="rounded-full bg-red-100 px-3 py-1 text-xs text-red-800">
                  {health.message}
                </span>
              )}
            </dd>
          </div>
        </dl>
      </main>
    </div>
  );
}
