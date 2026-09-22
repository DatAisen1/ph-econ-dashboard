"use client";

import { useRef, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
} from "recharts";
import type { CountryComparisonRow } from "@/lib/types";
import { downloadCsv, downloadChartAsPng } from "@/lib/chartExport";
import type { IndicatorMetadata } from "@/lib/indicatorMetadata";

// Fixed palette per country so a given country is always the same color
// across indicators - consistency matters more here than aesthetic
// variety, since the person comparing charts needs PHL to mean the same
// thing every time they see it.
const COUNTRY_COLORS: Record<string, string> = {
  PHL: "var(--color-institutional)",
  IDN: "var(--color-signal)",
  THA: "#7A9E7E",
  VNM: "#B0432F",
  KOR: "var(--color-muted)",
};

const COUNTRY_NAMES: Record<string, string> = {
  PHL: "Philippines",
  IDN: "Indonesia",
  THA: "Thailand",
  VNM: "Vietnam",
  KOR: "South Korea",
};

export default function CountryComparisonChart({
  series,
  indicatorId,
  indicatorMetadata,
  selectedCountries,
}: {
  series: CountryComparisonRow[];
  indicatorId: string;
  indicatorMetadata: IndicatorMetadata;
  selectedCountries: string[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [range, setRange] = useState<"recent" | "all">("recent");

  const latestYear = series.at(-1)?.year ?? 0;
  const chartSeries = range === "recent"
    ? series.filter((row) => row.year >= latestYear - 9)
    : series;

  const countryCodes = selectedCountries.filter((code) =>
    chartSeries.some((row) => row[code] !== undefined)
  );

  async function handlePngExport() {
    if (!containerRef.current) return;
    setIsExporting(true);
    try {
      await downloadChartAsPng(containerRef.current, `ph-compare-${indicatorId}.png`);
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div>
      <div className="flex justify-end gap-4 mb-2">
        <button
          onClick={() => downloadCsv(`ph-compare-${indicatorId}.csv`, series)}
          className="text-xs font-mono text-muted hover:text-ink transition-colors"
        >
          Download CSV
        </button>
        <button
          onClick={handlePngExport}
          disabled={isExporting}
          className="text-xs font-mono text-muted hover:text-ink transition-colors disabled:opacity-50"
        >
          {isExporting ? "Exporting..." : "Download PNG"}
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <p className="font-mono text-xs text-muted">
          {indicatorMetadata.frequency} observations &middot; {indicatorMetadata.unit}
        </p>
        <label className="flex items-center gap-2 text-xs text-muted">
          <span className="font-mono">TIME WINDOW</span>
          <select
            value={range}
            onChange={(event) => setRange(event.target.value as "recent" | "all")}
            className="border border-black/15 bg-surface px-2 py-1 text-xs text-ink"
          >
            <option value="recent">Recent comparison ({latestYear - 9}-{latestYear})</option>
            <option value="all">Full history ({series[0]?.year}-{latestYear})</option>
          </select>
        </label>
      </div>

      {countryCodes.length === 0 && <p className="text-sm text-muted py-8">Select at least one country to compare.</p>}

      {indicatorId === "FP.CPI.TOTL.ZG" && range === "recent" && countryCodes.length > 0 && (
        <p className="text-xs text-muted mb-3">
          The chart defaults to the latest 10 years for a readable current comparison. Full history remains available; it includes Indonesia&apos;s valid 1966 inflation observation of 1,136.3%.
        </p>
      )}

      <div ref={containerRef} className="w-full h-96 bg-surface">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartSeries} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
            <XAxis
              dataKey="year"
              tick={{ fontFamily: "var(--font-mono)", fontSize: 12, fill: "var(--color-muted)" }}
              tickLine={false}
              axisLine={{ stroke: "#E5E7EB" }}
            />
            <YAxis
              tick={{ fontFamily: "var(--font-mono)", fontSize: 12, fill: "var(--color-muted)" }}
              tickLine={false}
              axisLine={false}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{ fontFamily: "var(--font-sans)", borderRadius: 4, border: "1px solid #E5E7EB" }}
              labelStyle={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}
            />
            <Legend wrapperStyle={{ fontFamily: "var(--font-sans)", fontSize: 13 }} />
            {countryCodes.map((code) => (
              <Line
                key={code}
                type="monotone"
                dataKey={code}
                name={COUNTRY_NAMES[code] ?? code}
                stroke={COUNTRY_COLORS[code]}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
            <Brush dataKey="year" height={24} stroke="var(--color-institutional)" travellerWidth={8} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}