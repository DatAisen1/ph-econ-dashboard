"use client";

import { useMemo, useState } from "react";
import type { PhDetailRecord, RegionGeoJson } from "@/lib/types";

type RegionalMetric = "index" | "yoy" | "mom";

function numeric(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

function valueFor(
  data: PhDetailRecord[],
  region: string,
  date: string,
  metric: RegionalMetric,
): number | null {
  const index = data.findIndex((row) => row.date === date);
  if (index < 0) return null;
  const current = numeric(data[index][region]);
  if (current === null || metric === "index") return current;
  const comparisonIndex = metric === "yoy" ? index - 12 : index - 1;
  const comparison = comparisonIndex >= 0 ? numeric(data[comparisonIndex][region]) : null;
  if (comparison === null || comparison === 0) return null;
  return ((current - comparison) / comparison) * 100;
}

export default function RegionalComparisonTable({
  data,
  geojson,
  metric,
  onMetricChange,
}: {
  data: PhDetailRecord[];
  geojson: RegionGeoJson;
  metric: RegionalMetric;
  onMetricChange: (metric: RegionalMetric) => void;
}) {
  const [sortDescending, setSortDescending] = useState(true);
  const latestDate = data.at(-1)?.date ?? "";
  const rows = useMemo(() => {
    return geojson.features
      .map((feature) => {
        const region = feature.properties.psa_geolocation_name;
        return { region, value: valueFor(data, region, latestDate, metric) };
      })
      .sort((a, b) => {
        if (a.value === null) return 1;
        if (b.value === null) return -1;
        return sortDescending ? b.value - a.value : a.value - b.value;
      });
  }, [data, geojson, latestDate, metric, sortDescending]);

  const metricLabel = metric === "index" ? "CPI index" : metric === "yoy" ? "Year-over-year change" : "Month-over-month change";
  const unit = metric === "index" ? "2018 = 100" : "%";

  return (
    <section className="mt-16 border-t border-black/10 pt-10" aria-labelledby="regional-comparison">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-5">
        <div>
          <h2 id="regional-comparison" className="font-display text-xl">How does CPI vary across Philippine regions?</h2>
          <p className="text-sm text-muted mt-2">Ranking by {metricLabel.toLowerCase()} for {latestDate}. {unit}.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(["index", "yoy", "mom"] as RegionalMetric[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onMetricChange(option)}
              className={`text-xs font-mono px-3 py-1.5 border transition-colors ${metric === option ? "bg-institutional text-white border-institutional" : "text-muted border-black/15 hover:border-institutional"}`}
            >
              {option === "index" ? "CPI index" : option === "yoy" ? "YoY" : "MoM"}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setSortDescending((current) => !current)}
            className="text-xs font-mono px-3 py-1.5 border border-black/15 text-muted hover:border-institutional"
          >
            Sort {sortDescending ? "low to high" : "high to low"}
          </button>
        </div>
      </div>
      <div className="overflow-x-auto border-y border-black/10">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left font-mono text-xs text-muted">
              <th className="py-3 pr-4">Region</th>
              <th className="py-3 text-right">{metricLabel} ({unit})</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.region} className="border-t border-black/5">
                <td className="py-3 pr-4">{row.region}</td>
                <td className="py-3 text-right font-mono">{row.value === null ? "No data available" : `${row.value >= 0 && metric !== "index" ? "+" : ""}${row.value.toFixed(1)}${metric === "index" ? "" : "%"}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
