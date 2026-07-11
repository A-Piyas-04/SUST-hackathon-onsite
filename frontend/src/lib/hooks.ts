"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./api";
import { Async } from "./ui";

/**
 * Fetch-with-state hook. Returns the discriminated {@link Async} state plus a
 * `reload` callback. Optional `intervalMs` enables polling (used for the
 * dashboard refresh during demos — 3–5s per Phase 6 spec).
 *
 * `deps` is the caller's dependency array; a re-run refetches with a loading
 * state, while poll ticks refetch silently in the background.
 */
export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  intervalMs?: number,
): { state: Async<T>; reload: () => void } {
  const [state, setState] = useState<Async<T>>({ kind: "loading" });
  const [reloadTick, setReloadTick] = useState(0);
  const fetcherRef = useRef(fetcher);

  // Keep the latest fetcher without making it a render dependency.
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  useEffect(() => {
    let active = true;

    const load = async (showLoading: boolean) => {
      // Deferred a microtask so this is not a synchronous setState in the effect body.
      await Promise.resolve();
      if (!active) return;
      if (showLoading) setState({ kind: "loading" });
      try {
        const data = await fetcherRef.current();
        if (active) setState({ kind: "ready", data });
      } catch (err) {
        if (active)
          setState({
            kind: "error",
            error: err instanceof ApiError || err instanceof Error ? err : new Error("Unknown error"),
          });
      }
    };

    load(true);
    let timer: ReturnType<typeof setInterval> | undefined;
    if (intervalMs) timer = setInterval(() => load(false), intervalMs);

    return () => {
      active = false;
      if (timer) clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadTick, intervalMs]);

  const reload = useCallback(() => setReloadTick((t) => t + 1), []);
  return { state, reload };
}
