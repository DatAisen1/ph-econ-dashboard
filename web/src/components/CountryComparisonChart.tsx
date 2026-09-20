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

export default function CountryComparisonChart({
  series,
  indicatorLabel,
}: {
  series: CountryComparisonRow[];
  indicatorLabel: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);

  const countryCodes = Object.keys(COUNTRY_COLORS).filter((code) =>
    series.some((row) => row[code] !== undefined)
  );

  async function handlePngExport() {
    if (!containerRef.current) return;
    setIsExporting(true);
    try {
      await downloadChartAsPng(containerRef.current, `ph-compare-${indicatorLabel}.png`);
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div>
      <div className="flex justify-end gap-4 mb-2">
        <button
          onClick={() => downloadCsv(`ph-compare-${indicatorLabel}.csv`, series)}
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

      <div ref={containerRef} className="w-full h-96 bg-surface">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
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
                name={code}
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