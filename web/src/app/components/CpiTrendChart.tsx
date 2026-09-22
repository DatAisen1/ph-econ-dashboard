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

const NATIONAL_KEY = "PHILIPPINES";
const NATIONAL_COLOR = "var(--color-institutional)";
const SELECTED_COLOR = "var(--color-signal)";

export default function CpiTrendChart({
  data,
  selectedRegion,
  selectedRegionLabel,
}: {
  data: PhDetailRecord[];
  selectedRegion?: string | null; // the exact psa_geolocation_name key, or null
  selectedRegionLabel?: string; // short display label, e.g. "Region III"
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

            {/* National line: always shown, the constant baseline. */}
            <Line
              type="monotone"
              dataKey={NATIONAL_KEY}
              name="Philippines (national)"
              stroke={NATIONAL_COLOR}
              strokeWidth={2.5}
              dot={false}
              connectNulls
            />

            {/* Selected region's line: only rendered when a region is
                picked on the map. With 18 possible regions, showing all
                of them at once would be unreadable - one at a time
                against the national baseline is the actual comparison
                a viewer wants to make. */}
            {selectedRegion && (
              <Line
                type="monotone"
                dataKey={selectedRegion}
                name={selectedRegionLabel ?? selectedRegion}
                stroke={SELECTED_COLOR}
                strokeWidth={2.5}
                dot={false}
                connectNulls
              />
            )}

            <Brush dataKey="date" height={24} stroke="var(--color-institutional)" travellerWidth={8} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}