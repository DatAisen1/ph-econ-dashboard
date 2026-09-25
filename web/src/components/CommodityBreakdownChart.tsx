"use client";

import { useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { downloadChartAsPng } from "@/lib/chartExport";
import type { PhCommodityRecord } from "@/lib/types";
import { useDashboardFilters } from "./DashboardFilters";
type CommodityMetric = "index" | "yoy" | "mom";

const COMMODITY_LABELS: Record<string, string> = {
  "01 - FOOD AND NON-ALCOHOLIC BEVERAGES": "Food",
  "02 - ALCOHOLIC BEVERAGES AND TOBACCO": "Alcohol & tobacco",
  "03 - CLOTHING AND FOOTWEAR": "Clothing",
  "04 - HOUSING, WATER, ELECTRICITY, GAS, AND OTHER FUELS": "Housing & utilities",
  "05 - FURNISHINGS, HOUSEHOLD EQUIPMENT AND ROUTINE HOUSEHOLD MAINTENANCE": "Household",
  "06 - HEALTH": "Health",
  "07 - TRANSPORT": "Transport",
  "08 - INFORMATION AND COMMUNICATION": "Information & communication",
  "09 - RECREATION, SPORT AND CULTURE": "Recreation & culture",
  "10 - EDUCATION SERVICES": "Education",
  "11 - RESTAURANTS AND ACCOMMODATION SERVICES": "Restaurants & accommodation",
  "12 - FINANCIAL SERVICES": "Financial services",
  "13 - PERSONAL CARE, AND MISCELLANEOUS GOODS AND SERVICES": "Personal care & misc.",
};

function numericValue(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export default function CommodityBreakdownChart({
  data,
  regions,
}: {
  data: PhCommodityRecord[];
  regions: string[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);
  const { selectedRegion, metric, setSelectedRegion, setMetric } = useDashboardFilters();
  const activeRegion = selectedRegion ?? "PHILIPPINES";
  const uniqueRegions = [...new Set(regions)];

  const commodityKeys = useMemo(
    () => Object.keys(COMMODITY_LABELS).filter((key) => data.some((row) => key in row)),
    [data],
  );
  const latestDate = data.reduce((latest, row) => (row.date > latest ? row.date : latest), "");
  const chartData = useMemo(() => {
    const rowIndex = data.findIndex(
      (item) => item.date === latestDate && item.geolocation_name === activeRegion,
    );
    const row = rowIndex >= 0 ? data[rowIndex] : undefined;
    const comparisonYoyDate = `${Number(latestDate.slice(0, 4)) - 1}${latestDate.slice(4)}`;
    const month = Number(latestDate.slice(5));
    const comparisonMomDate = month === 1 ? `${Number(latestDate.slice(0, 4)) - 1}-12` : `${latestDate.slice(0, 5)}${String(month - 1).padStart(2, "0")}`;
    const comparisonYoy = data.find((item) => item.date === comparisonYoyDate && item.geolocation_name === activeRegion);
    const comparisonMom = data.find((item) => item.date === comparisonMomDate && item.geolocation_name === activeRegion);
    const rows = commodityKeys.map((key) => {
        const current = numericValue(row?.[key]);
        const previousYoy = numericValue(comparisonYoy?.[key]);
        const previousMom = numericValue(comparisonMom?.[key]);
        const yoy = current === null || previousYoy === null || previousYoy === 0 ? null : ((current - previousYoy) / previousYoy) * 100;
        const mom = current === null || previousMom === null || previousMom === 0 ? null : ((current - previousMom) / previousMom) * 100;
        return { name: COMMODITY_LABELS[key], value: metric === "index" ? current : metric === "yoy" ? yoy : mom, index: current, yoy, mom };
      });
    return rows
      .filter((item) => item.value !== null);
  }, [activeRegion, commodityKeys, data, latestDate, metric]);

  async function handlePngExport() {
    if (!containerRef.current) return;
    setIsExporting(true);
    try {
      await downloadChartAsPng(containerRef.current, "ph-cpi-commodity-breakdown.png");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <section className="mt-16 border-t border-black/10 pt-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-6">
        <div>
          <p className="font-mono text-xs text-muted tracking-wide mb-2">
            LATEST INDEX &middot; {latestDate}
          </p>
          <h2 className="font-display text-xl">{metric === "index" ? "How have prices changed across household categories?" : metric === "yoy" ? "Year-over-year change by category" : "Month-over-month change by category"}</h2>
          <p className="text-sm text-muted mt-2">
            Compare {metric === "index" ? "CPI index levels" : metric === "yoy" ? "annual changes" : "monthly changes"} across categories for one geography. This shows measured changes, not contributions to inflation.
          </p>
        </div>
        <label className="flex flex-col items-start gap-2 text-sm md:flex-row md:items-center">
          <span className="font-mono text-xs text-muted">GEOGRAPHY</span>
          <select
            value={activeRegion}
            onChange={(event) => setSelectedRegion(event.target.value)}
            className="w-full max-w-full border border-black/15 bg-surface px-3 py-2 text-sm text-ink md:w-auto"
          >
            {uniqueRegions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="flex flex-wrap gap-2 mb-4">
        {(["index", "yoy", "mom"] as CommodityMetric[]).map((option) => (
          <button key={option} type="button" onClick={() => setMetric(option)} className={`text-xs font-mono px-3 py-1.5 border ${metric === option ? "bg-institutional text-white border-institutional" : "text-muted border-black/15"}`}>
            {option === "index" ? "CPI index" : option === "yoy" ? "YoY" : "MoM"}
          </button>
        ))}
        <span className="font-mono text-xs text-muted self-center">{metric === "index" ? "2018 = 100" : "%"} &middot; {latestDate}</span>
      </div>
      <div className="flex justify-end gap-4 mb-2">
        <button
          onClick={handlePngExport}
          disabled={isExporting}
          className="text-xs font-mono text-muted hover:text-ink transition-colors disabled:opacity-50"
        >
          {isExporting ? "Exporting..." : "Download PNG"}
        </button>
      </div>
      <div ref={containerRef} className="w-full h-[29rem] bg-surface">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 8, right: 24, bottom: 8, left: 12 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
            <XAxis
              type="number"
              domain={["auto", "auto"]}
              tick={{ fontFamily: "var(--font-mono)", fontSize: 12, fill: "var(--color-muted)" }}
              tickLine={false}
              axisLine={{ stroke: "#E5E7EB" }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tick={{ fontFamily: "var(--font-sans)", fontSize: 12, fill: "var(--color-ink)" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value) => [Number(value).toFixed(1), metric === "index" ? "CPI index" : metric === "yoy" ? "YoY %" : "MoM %"]}
              contentStyle={{
                fontFamily: "var(--font-sans)",
                borderRadius: 4,
                border: "1px solid #E5E7EB",
              }}
            />
            <Bar dataKey="value" fill="var(--color-institutional)" radius={[0, 2, 2, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto mt-5 border-y border-black/10">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left font-mono text-xs text-muted">
              <th className="py-3 pr-4">Category</th>
              <th className="py-3 text-right">CPI index</th>
              <th className="py-3 text-right">YoY</th>
              <th className="py-3 text-right">MoM</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((item) => (
              <tr key={item.name} className="border-t border-black/5">
                <td className="py-3 pr-4">{item.name}</td>
                <td className="py-3 text-right font-mono">{item.index === null ? "No data" : item.index.toFixed(1)}</td>
                <td className="py-3 text-right font-mono">{item.yoy === null ? "No data" : `${item.yoy >= 0 ? "+" : ""}${item.yoy.toFixed(1)}%`}</td>
                <td className="py-3 text-right font-mono">{item.mom === null ? "No data" : `${item.mom >= 0 ? "+" : ""}${item.mom.toFixed(1)}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="font-mono text-xs text-muted mt-3">2018 = 100 &middot; {activeRegion}</p>
    </section>
  );
}