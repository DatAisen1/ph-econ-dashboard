"use client";

import { useState } from "react";
import PhZoneMap from "./PhZoneMap";
import CpiTrendChart from "./CpiTrendChart";
import ChangeBadge from "./ChangeBadge";
import type { PhDetailRecord } from "@/lib/types";
import type { ChangeResult } from "@/lib/format";

const ZONE_TO_CHART_KEY: Record<string, string> = {
  NCR: "National Capital Region (NCR)",
  AONCR: "Areas Outside National Capital Region (AONCR)",
};

export default function DashboardHero({
  phDetail,
  geojson,
  latestDate,
  latestNational,
  momChange,
  yoyChange,
}: {
  phDetail: PhDetailRecord[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  geojson: any;
  latestDate: string;
  latestNational: number;
  momChange: ChangeResult | null;
  yoyChange: ChangeResult | null;
}) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

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
              ? `Showing ${selectedZone === "NCR" ? "National Capital Region" : "Areas Outside NCR"} in the chart below.`
              : "Click a zone on the map to highlight it in the chart below."}
          </p>
        </div>
        <div className="flex justify-center">
          <PhZoneMap
            geojson={geojson}
            phDetail={phDetail}
            selectedZone={selectedZone}
            onSelectZone={(zoneId) =>
              setSelectedZone((current) => (current === zoneId ? null : zoneId))
            }
          />
        </div>
      </div>

      <section>
        <h2 className="font-display text-xl mb-6">
          CPI trend, National Capital Region and rest of the country
        </h2>
        <CpiTrendChart
          data={phDetail}
          highlightKey={selectedZone ? ZONE_TO_CHART_KEY[selectedZone] : null}
        />
      </section>
    </>
  );
}