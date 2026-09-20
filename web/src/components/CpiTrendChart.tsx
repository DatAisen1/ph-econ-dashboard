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
import type { PhDetailRecord } from "@/lib/types";
import { downloadCsv, downloadChartAsPng } from "@/lib/chartExport";

const SERIES = [
  { key: "PHILIPPINES", label: "Philippines (national)", color: "var(--color-institutional)" },
  { key: "National Capital Region (NCR)", label: "NCR", color: "var(--color-signal)" },
  { key: "Areas Outside National Capital Region (AONCR)", label: "AONCR", color: "var(--color-muted)" },
] as const;

export default function CpiTrendChart({
  data,
  highlightKey,
}: {
  data: PhDetailRecord[];
  highlightKey?: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);

  async function handlePngExport() {
    if (!containerRef.current) return;
    setIsExporting(true);
    try {
      await downloadChartAsPng(containerRef.current, "ph-cpi-trend.png");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div>
      <div className="flex justify-end gap-4 mb-2">
        <button
          onClick={() => downloadCsv("ph-cpi-trend.csv", data)}
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
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontFamily: "var(--font-mono)", fontSize: 12, fill: "var(--color-muted)" }}
              tickLine={false}
              axisLine={{ stroke: "#E5E7EB" }}
              minTickGap={40}
            />
            <YAxis
              tick={{ fontFamily: "var(--font-mono)", fontSize: 12, fill: "var(--color-muted)" }}
              tickLine={false}
              axisLine={false}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                fontFamily: "var(--font-sans)",
                borderRadius: 4,
                border: "1px solid #E5E7EB",
              }}
              labelStyle={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}
            />
            <Legend wrapperStyle={{ fontFamily: "var(--font-sans)", fontSize: 13 }} />
            {SERIES.map((s) => {
              const isDimmed = highlightKey != null && s.key !== highlightKey;
              return (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={isDimmed ? 1 : 2.5}
                  strokeOpacity={isDimmed ? 0.35 : 1}
                  dot={false}
                  connectNulls
                />
              );
            })}
            {/* Brush = the zoom / date-range control. Recharts renders it
                as a mini overview chart below the main one - drag the
                handles to zoom into a range. Native to Recharts, no
                extra dependency needed. */}
            <Brush
              dataKey="date"
              height={24}
              stroke="var(--color-institutional)"
              travellerWidth={8}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}