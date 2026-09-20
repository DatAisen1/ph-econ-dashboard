import type { ChangeResult } from "@/lib/format";

export default function ChangeBadge({ change, label }: { change: ChangeResult | null; label: string }) {
  if (!change) {
    return <span className="text-xs text-muted font-mono">{label}: n/a</span>;
  }

  const color =
    change.direction === "up"
      ? "text-alert" // rising prices = alert color, semantically consistent with the palette's original intent
      : change.direction === "down"
        ? "text-institutional"
        : "text-muted";
  const arrow = change.direction === "up" ? "\u2191" : change.direction === "down" ? "\u2193" : "\u2192";

  return (
    <span className={`text-xs font-mono ${color}`}>
      {label}: {arrow} {Math.abs(change.percent).toFixed(1)}%
    </span>
  );
}