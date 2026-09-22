"use client";

import { useState } from "react";
import PhZoneMap from "./PhZoneMap";
import CpiTrendChart from "./CpiTrendChart";
import ChangeBadge from "./ChangeBadge";
import type { PhDetailRecord, RegionGeoJson } from "@/lib/types";
import type { ChangeResult } from "@/lib/format";

export default function DashboardHero({
  phDetail,
  geojson,
  latestDate,
  latestNational,
  momChange,
  yoyChange,
}: {
  phDetail: PhDetailRecord[];
  geojson: RegionGeoJson;
  latestDate: string;
  latestNational: number;
  momChange: ChangeResult | null;
  yoyChange: ChangeResult | null;
}) {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  // Look up the short display label for whichever region is selected -
  // the map only gives us the data key (psa_geolocation_name) on click,
  // this finds its matching short label ("Region III", "NCR", etc.) for
  // display text and the chart legend.
  const selectedFeature = geojson.features.find(
    (f) => f.properties.psa_geolocation_name === selectedRegion
  );
  const selectedLabel = selectedFeature?.properties.zone_id;

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
            {selectedLabel
              ? `Comparing ${selectedLabel} against the national trend below.`
              : "Click a region on the map to compare it against the national trend below."}
          </p>
        </div>
        <div className="flex justify-center">
          <PhZoneMap
            geojson={geojson}
            phDetail={phDetail}
            selectedZone={selectedRegion}
            onSelectZone={(psaGeolocationName) =>
              setSelectedRegion((current) =>
                current === psaGeolocationName ? null : psaGeolocationName
              )
            }
          />
        </div>
      </div>

      <section>
        <h2 className="font-display text-xl mb-6">
          {selectedLabel
            ? `CPI trend, ${selectedLabel} vs. national`
            : "CPI trend, national"}
        </h2>
        <CpiTrendChart data={phDetail} selectedRegion={selectedRegion} selectedRegionLabel={selectedLabel} />
      </section>
    </>
  );
}