// Pure functions, no React/DOM dependency - testable in isolation if we
// ever add a JS test runner. Kept separate from components for the same
// reason export/transform_export.py splits pure transforms from I/O.

export type ChangeResult = {
  absolute: number;
  percent: number;
  direction: "up" | "down" | "flat";
};

export function computeChange(current: number | null, previous: number | null): ChangeResult | null {
  if (current === null || previous === null || previous === 0) return null;
  const absolute = current - previous;
  const percent = (absolute / previous) * 100;
  return {
    absolute,
    percent,
    direction: absolute > 0.001 ? "up" : absolute < -0.001 ? "down" : "flat",
  };
}

export function formatDateLabel(isoDate: string): string {
  // "YYYY-MM" -> "Jan 2018". Plain string handling, deliberately not
  // using Date() parsing here - "2018-01" parsed as a Date can shift a
  // day depending on the runtime's timezone, which is exactly the kind
  // of subtle bug that's easy to miss until someone's viewing the site
  // from a different timezone than whoever tested it.
  const [year, month] = isoDate.split("-");
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const monthIndex = parseInt(month, 10) - 1;
  return `${MONTHS[monthIndex]} ${year}`;
}

export function formatRelativeTime(isoTimestamp: string): string {
  const then = new Date(isoTimestamp).getTime();
  const now = Date.now();
  const diffHours = Math.round((now - then) / (1000 * 60 * 60));
  if (diffHours < 1) return "just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}