"use client";

import { useState } from "react";
import CountryComparisonChart from "./CountryComparisonChart";
import ChangeBadge from "./ChangeBadge";
import { computeChange } from "@/lib/format";
import type { CountryComparisonData } from "@/lib/types";

export default function CompareView({ data }: { data: CountryComparisonData }) {
  const indicatorCodes = Object.keys(data);
  const [selected, setSelected] = useState(indicatorCodes[0]);

  const indicator = data[selected];
  const series = indicator.series;
  const latest = series[series.length - 1];
  const previous = series.length > 1 ? series[series.length - 2] : null;

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-8">
        {indicatorCodes.map((code) => (
          <button
            key={code}
            onClick={() => setSelected(code)}
            className={`text-sm font-mono px-3 py-1.5 rounded border transition-colors ${
              code === selected
                ? "bg-institutional text-white border-institutional"
                : "text-muted border-gray-200 hover:border-institutional"
            }`}
          >
            {data[code].indicator_name}
          </button>
        ))}
      </div>

      {latest && (
        <div className="flex flex-wrap gap-4 mb-6">
          {Object.keys(latest)
            .filter((k) => k !== "year")
            .map((countryCode) => {
              const currentVal = latest[countryCode];
              const previousVal = previous ? previous[countryCode] : null;
              const change = computeChange(
                typeof currentVal === "number" ? currentVal : null,
                typeof previousVal === "number" ? previousVal : null
              );
              return <ChangeBadge key={countryCode} change={change} label={`${countryCode} YoY`} />;
            })}
        </div>
      )}

      <CountryComparisonChart series={series} indicatorLabel={indicator.indicator_name} />
    </div>
  );
}