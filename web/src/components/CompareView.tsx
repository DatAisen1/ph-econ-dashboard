"use client";

import { useState } from "react";
import CountryComparisonChart from "./CountryComparisonChart";
import { getIndicatorMetadata } from "@/lib/indicatorMetadata";
import type { CountryComparisonData } from "@/lib/types";

const COUNTRY_NAMES: Record<string, string> = {
  PHL: "Philippines",
  IDN: "Indonesia",
  THA: "Thailand",
  VNM: "Vietnam",
  KOR: "South Korea",
};

function formatValue(value: number, format: "percent" | "usd" | "constant-usd"): string {
  if (format === "percent") return `${value.toFixed(1)}%`;
  return `$${Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value)}`;
}

export default function CompareView({ data }: { data: CountryComparisonData }) {
  const indicatorCodes = Object.keys(data);
  const [selected, setSelected] = useState(indicatorCodes[0]);
  const allCountries = Object.keys(data[selected]?.series.at(-1) ?? {}).filter((key) => key !== "year");
  const [selectedCountries, setSelectedCountries] = useState<string[]>(allCountries);
  const [resetToken, setResetToken] = useState(0);

  const indicator = data[selected];
  const indicatorMetadata = getIndicatorMetadata(selected);
  const series = indicator.series;
  const latest = series[series.length - 1];
  const previous = series.length > 1 ? series[series.length - 2] : null;

  function selectIndicator(code: string) {
    setSelected(code);
    const countries = Object.keys(data[code].series.at(-1) ?? {}).filter((key) => key !== "year");
    setSelectedCountries(countries);
  }

  function toggleCountry(code: string) {
    setSelectedCountries((current) => current.includes(code) ? current.filter((value) => value !== code) : [...current, code]);
  }

  function resetFilters() {
    setSelected(indicatorCodes[0]);
    setSelectedCountries(Object.keys(data[indicatorCodes[0]].series.at(-1) ?? {}).filter((key) => key !== "year"));
    setResetToken((value) => value + 1);
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-8">
        {indicatorCodes.map((code) => (
          <button
            key={code}
            onClick={() => selectIndicator(code)}
            className={`text-sm font-mono px-3 py-1.5 rounded border transition-colors ${
              code === selected
                ? "bg-institutional text-white border-institutional"
                : "text-muted border-gray-200 hover:border-institutional"
            }`}
          >
            {getIndicatorMetadata(code).name}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        <span className="font-mono text-xs text-muted mr-1">COUNTRIES</span>
        {allCountries.map((code) => (
          <button key={code} type="button" onClick={() => toggleCountry(code)} className={`text-xs px-2.5 py-1 border ${selectedCountries.includes(code) ? "border-institutional text-institutional" : "border-black/15 text-muted"}`}>
            {COUNTRY_NAMES[code] ?? code}
          </button>
        ))}
        <button type="button" onClick={resetFilters} className="text-xs font-mono text-muted border border-black/15 px-3 py-1 hover:border-institutional ml-auto">Reset filters</button>
      </div>

      <section className="border-y border-black/10 py-6 mb-8">
        <h2 className="font-display text-xl mb-2">What does this mean?</h2>
        <p className="text-sm text-muted leading-relaxed max-w-3xl">
          {indicatorMetadata.whatItMeans} {indicatorMetadata.description} These are annual observations, so the latest year is compared with the preceding year where shown.
        </p>
      </section>

      {latest && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5 mb-10">
          {Object.keys(latest)
            .filter((key) => selectedCountries.includes(key) && typeof latest[key] === "number")
            .map((countryCode) => {
              const currentValue = latest[countryCode] as number;
              const previousValue = previous?.[countryCode];
              const difference = typeof previousValue === "number" ? currentValue - previousValue : null;
              return (
                <div key={countryCode} className="border border-black/10 bg-surface px-4 py-4">
                  <p className="text-sm text-muted">{COUNTRY_NAMES[countryCode] ?? countryCode}</p>
                  <p className="font-mono text-xl mt-2">{formatValue(currentValue, indicatorMetadata.format)}</p>
                  <p className="font-mono text-xs text-muted mt-1">
                    {indicatorMetadata.name} &middot; {latest.year} &middot; {indicatorMetadata.unit}
                  </p>
                  {difference !== null && previous && (
                    <p className="font-mono text-xs text-muted mt-2">
                      vs. {previous.year}: {difference >= 0 ? "+" : ""}{difference.toFixed(1)} {indicatorMetadata.format === "percent" ? "percentage points" : indicatorMetadata.unit}
                    </p>
                  )}
                </div>
              );
            })}
        </div>
      )}

      <section className="mb-4">
        <h2 className="font-display text-xl">{indicatorMetadata.chartTitle}</h2>
        <p className="text-sm text-muted mt-2">
          {indicatorMetadata.chartSubtitle} Unit: {indicatorMetadata.unit}. Source: {indicatorMetadata.source}.
        </p>
      </section>
      <CountryComparisonChart
        key={resetToken}
        series={series}
        indicatorId={selected}
        indicatorMetadata={indicatorMetadata}
        selectedCountries={selectedCountries}
      />
    </div>
  );
}