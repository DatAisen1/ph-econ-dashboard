"use client";

import { useSyncExternalStore } from "react";
import { formatRelativeTime } from "@/lib/format";

/**
 * "time since X" is a value that's legitimately different depending on
 * WHEN it's computed - the server's render pass and the client's
 * hydration pass happen at different moments, so computing it directly
 * during render (or via a plain useEffect + setState) either causes a
 * hydration mismatch or trips React's "no setState synchronously in an
 * effect" lint rule. useSyncExternalStore is the actual mechanism React
 * provides for exactly this case: a value that can differ between the
 * server snapshot and the client snapshot, with a defined subscription
 * for staying current.
 *
 * subscribe: re-renders the consumer every 60s so "5m ago" ticks forward
 * on its own, without a page reload.
 */
function subscribe(callback: () => void) {
  const interval = setInterval(callback, 60_000);
  return () => clearInterval(interval);
}

export default function LastUpdated({ isoTimestamp }: { isoTimestamp: string }) {
  const relative = useSyncExternalStore(
    subscribe,
    () => formatRelativeTime(isoTimestamp), // client snapshot
    () => null // server snapshot - no "now" exists yet during SSR
  );

  return (
    <span className="text-xs font-mono text-muted">
      Data last refreshed: {relative ?? "..."}
    </span>
  );
}