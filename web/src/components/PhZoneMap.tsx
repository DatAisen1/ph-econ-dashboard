"use client";

import { useMemo, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { PhDetailRecord } from "@/lib/types";

type ZoneFeature = {
  type: "Feature";
  properties: { zone_id: string; psa_geolocation_name: string };
  geometry: GeoJSON.Geometry;
};

type ZoneGeoJson = {
  type: "FeatureCollection";
  features: ZoneFeature[];
};

export type MapMetric = "index" | "yoy" | "mom";

function getZoneValue(data: PhDetailRecord[], regionName: string, metric: MapMetric): number | null {
  const current = data.at(-1)?.[regionName];
  if (typeof current !== "number" || metric === "index") return typeof current === "number" ? current : null;
  const comparison = data.at(-(metric === "yoy" ? 13 : 2))?.[regionName];
  if (typeof comparison !== "number" || comparison === 0) return null;
  return ((current - comparison) / comparison) * 100;
}

function getComparisonDate(data: PhDetailRecord[], metric: MapMetric): string | null {
  if (metric === "index") return null;
  return data.at(-(metric === "yoy" ? 13 : 2))?.date ?? null;
}

export default function PhZoneMap({
  geojson,
  phDetail,
  selectedZone,
  onSelectZone,
  metric,
}: {
  geojson: ZoneGeoJson;
  phDetail: PhDetailRecord[];
  selectedZone: string | null;
  onSelectZone: (zoneId: string) => void;
  metric: MapMetric;
}) {
  const width = 400;
  const height = 520;
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);

  const { pathFor, zoneValues } = useMemo(() => {
    const projection = geoMercator().fitSize([width, height], geojson as unknown as GeoJSON.GeoJSON);
    const pathGenerator = geoPath(projection);

    const values: Record<string, number | null> = {};
    for (const f of geojson.features) {
      values[f.properties.zone_id] = getZoneValue(phDetail, f.properties.psa_geolocation_name, metric);
    }

    return {
      pathFor: (feature: ZoneFeature) => pathGenerator(feature as unknown as GeoJSON.Feature) ?? "",
      zoneValues: values,
    };
  }, [geojson, phDetail, metric]);

  // Fill intensity reflects the actual CPI value, not a decorative
  // palette - the map itself is a data encoding, per the design
  // principle we set: "data is the hero, not decoration."
  const numericValues = Object.values(zoneValues).filter((v): v is number => v !== null);
  const minVal = numericValues.length ? Math.min(...numericValues) : 0;
  const maxVal = numericValues.length ? Math.max(...numericValues) : 0;

  function fillFor(zoneId: string): string {
    const v = zoneValues[zoneId];
    if (v === null) return "#D1D5DB";
    if (minVal === maxVal) return "var(--color-institutional)";
    const t = (v - minVal) / (maxVal - minVal); // 0..1
    // Interpolate between a lighter and darker institutional navy so a
    // higher CPI reads as visually "heavier" - consistent, legible signal.
    const lightness = 55 - t * 25; // 55% (lighter) -> 30% (darker)
    return `hsl(209, 45%, ${lightness}%)`;
  }

  const hoveredFeature = geojson.features.find((feature) => feature.properties.zone_id === hoveredZone);
  const latestDate = phDetail.at(-1)?.date ?? "Unavailable";
  const metricLabel = metric === "index" ? "Regional CPI index" : metric === "yoy" ? "Year-over-year change" : "Month-over-month change";
  const unit = metric === "index" ? "2018 = 100" : "%";
  const comparisonDate = getComparisonDate(phDetail, metric);

  return (
    <div className="relative w-full max-w-sm">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        role="img"
        aria-label={`${metricLabel} map of the Philippines' 18 regions`}
      >
      {geojson.features.map((feature) => {
        const zoneId = feature.properties.zone_id;
        const isSelected = selectedZone === zoneId;
        return (
          <path
            key={zoneId}
            d={pathFor(feature)}
            fill={fillFor(zoneId)}
            stroke="var(--color-surface)"
            strokeWidth={isSelected ? 2 : 1}
            className="cursor-pointer transition-all duration-150 ease-out hover:opacity-90"
            style={{
              filter: isSelected ? "drop-shadow(0 4px 8px rgba(0,0,0,0.25))" : "none",
              transformOrigin: "center",
              transform: isSelected ? "scale(1.02)" : "scale(1)",
            }}
            onClick={() => onSelectZone(zoneId)}
            onMouseEnter={() => setHoveredZone(zoneId)}
            onMouseLeave={() => setHoveredZone(null)}
            tabIndex={0}
            role="button"
            aria-pressed={isSelected}
            aria-label={`${feature.properties.psa_geolocation_name}, ${metricLabel} ${zoneValues[zoneId]?.toFixed(1) ?? "unavailable"}, ${unit}, ${latestDate}`}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onSelectZone(zoneId);
            }}
          />
        );
      })}
      </svg>
      {hoveredFeature && (
        <div className="pointer-events-none absolute left-2 top-2 max-w-[15rem] border border-black/10 bg-surface/95 px-3 py-2 text-xs shadow-sm">
          <p className="font-medium text-ink">{hoveredFeature.properties.psa_geolocation_name}</p>
          <p className="font-mono text-muted mt-1">{metricLabel}: {zoneValues[hoveredZone ?? ""] === null ? "No data available" : `${zoneValues[hoveredZone ?? ""]?.toFixed(1)}${metric === "index" ? "" : "%"}`}</p>
          {comparisonDate && <p className="font-mono text-muted">Compared with: {comparisonDate}</p>}
          <p className="font-mono text-muted">Latest available: {latestDate}</p>
        </div>
      )}
      <div className="mt-2 text-xs font-mono text-muted">
        <p>{metricLabel} &middot; {unit}</p>
        <div className="flex items-center gap-2 mt-1"><span>Lower</span><span className="h-2 flex-1 bg-gradient-to-r from-[#D1D5DB] to-[#1B3A5C]" /><span>Higher</span></div>
      </div>
    </div>
  );
}