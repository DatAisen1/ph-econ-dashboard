"use client";

import { useState } from "react";
import PhZoneMap, { type MapMetric } from "./PhZoneMap";
import CpiTrendChart from "./CpiTrendChart";
import CpiKpiSection from "./CpiKpiSection";
import CpiUnderstanding from "./CpiUnderstanding";
import CommodityBreakdownChart from "./CommodityBreakdownChart";
import RegionalComparisonTable from "./RegionalComparisonTable";
import ChangeBadge from "./ChangeBadge";
import type { PhCommodityRecord, PhDetailRecord } from "@/lib/types";
import type { ChangeResult } from "@/lib/format";

export default function DashboardHero({
  phDetail,
  phCommodity,
  geojson,
  latestDate,
  latestNational,
  momChange,
  yoyChange,
}: {
  phDetail: PhDetailRecord[];
  phCommodity: PhCommodityRecord[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  geojson: any;
  latestDate: string;
  latestNational: number;
  momChange: ChangeResult | null;
  yoyChange: ChangeResult | null;
}) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [metric, setMetric] = useState<MapMetric>("index");
  const [resetToken, setResetToken] = useState(0);
  const selectedRegion = selectedZone
    ? geojson.features.find((feature: { properties: { zone_id: string } }) => feature.properties.zone_id === selectedZone)
        ?.properties.psa_geolocation_name ?? null
    : null;

  return (
    <>
      <div className="grid md:grid-cols-2 gap-12 items-start mb-16">
        <div>
          <p className="font-mono text-xs text-muted tracking-wide mb-4">
            Philippine Statistics Authority &middot; Consumer Price Index
          </p>
          <h1 className="font-display text-4xl md:text-5xl leading-tight mb-6">
            How much has everyday life gotten more expensive in the Philippines?
          </h1>
          <p className="text-lg text-muted">
            As of <span className="font-mono text-ink">{latestDate}</span>, the national
            consumer price index stands at{" "}
            <span className="font-mono text-institutional font-medium">
              {latestNational.toFixed(1)}
            </span>{" "}
            (2018 = 100).
          </p>
          <div className="flex gap-4 mt-3">
            <ChangeBadge change={momChange} label="MoM" />
            <ChangeBadge change={yoyChange} label="YoY" />
          </div>
          <p className="text-sm text-muted mt-6">
            {selectedZone
              ? `Showing ${selectedRegion ?? "the selected region"} against the national index below.`
              : "Click a region on the map to highlight it against the national index below."}
          </p>
        </div>
        <div className="flex justify-center">
          <PhZoneMap
            geojson={geojson}
            phDetail={phDetail}
            selectedZone={selectedZone}
            metric={metric}
            onSelectZone={(zoneId) =>
              setSelectedZone((current) => (current === zoneId ? null : zoneId))
            }
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
        <div>
          <p className="font-mono text-xs text-muted">MAP METRIC</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {(["index", "yoy", "mom"] as MapMetric[]).map((option) => (
              <button key={option} type="button" onClick={() => setMetric(option)} className={`text-xs font-mono px-3 py-1.5 border ${metric === option ? "bg-institutional text-white border-institutional" : "text-muted border-black/15"}`}>
                {option === "index" ? "CPI index" : option === "yoy" ? "YoY" : "MoM"}
              </button>
            ))}
          </div>
        </div>
        <button type="button" onClick={() => { setSelectedZone(null); setMetric("index"); setResetToken((value) => value + 1); }} className="text-xs font-mono text-muted border border-black/15 px-3 py-1.5 hover:border-institutional">
          Reset filters
        </button>
      </div>

      <CpiKpiSection phDetail={phDetail} phCommodity={phCommodity} />
      <CpiUnderstanding latestValue={latestNational} latestDate={latestDate} />

      <section>
        <h2 className="font-display text-xl">How has the price level changed since 2018?</h2>
        <p className="text-sm text-muted mt-2 mb-6">
          Consumer Price Index (CPI), where 2018 = 100. The national series is shown with the selected region when one is highlighted.
        </p>
        <CpiTrendChart
          data={phDetail}
          highlightKey={selectedRegion}
        />
      </section>

      <RegionalComparisonTable key={`regional-${resetToken}`} data={phDetail} geojson={geojson} metric={metric} onMetricChange={setMetric} />
      <CommodityBreakdownChart key={`commodity-${resetToken}`} data={phCommodity} regions={["PHILIPPINES", ...geojson.features.map((feature: { properties: { psa_geolocation_name: string } }) => feature.properties.psa_geolocation_name)]} />
    </>
  );
}