"use client";

import { useMemo } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { PhDetailRecord } from "@/lib/types";

type ZoneFeature = {
  type: "Feature";
  properties: { zone_id: string; zone_label: string };
  geometry: GeoJSON.Geometry;
};

type ZoneGeoJson = {
  type: "FeatureCollection";
  features: ZoneFeature[];
};

const ZONE_COLUMN: Record<string, keyof PhDetailRecord> = {
  NCR: "National Capital Region (NCR)",
  AONCR: "Areas Outside National Capital Region (AONCR)",
};

function getLatestZoneValue(data: PhDetailRecord[], zoneId: string): number | null {
  const column = ZONE_COLUMN[zoneId];
  for (let i = data.length - 1; i >= 0; i--) {
    const v = data[i][column];
    if (typeof v === "number") return v;
  }
  return null;
}

export default function PhZoneMap({
  geojson,
  phDetail,
  selectedZone,
  onSelectZone,
}: {
  geojson: ZoneGeoJson;
  phDetail: PhDetailRecord[];
  selectedZone: string | null;
  onSelectZone: (zoneId: string) => void;
}) {
  const width = 400;
  const height = 520;

  const { pathFor, zoneValues } = useMemo(() => {
    const projection = geoMercator().fitSize([width, height], geojson as unknown as GeoJSON.GeoJSON);
    const pathGenerator = geoPath(projection);

    const values: Record<string, number | null> = {};
    for (const f of geojson.features) {
      values[f.properties.zone_id] = getLatestZoneValue(phDetail, f.properties.zone_id);
    }

    return {
      pathFor: (feature: ZoneFeature) => pathGenerator(feature as unknown as GeoJSON.Feature) ?? "",
      zoneValues: values,
    };
  }, [geojson, phDetail]);

  // Fill intensity reflects the actual CPI value, not a decorative
  // palette - the map itself is a data encoding, per the design
  // principle we set: "data is the hero, not decoration."
  const numericValues = Object.values(zoneValues).filter((v): v is number => v !== null);
  const minVal = Math.min(...numericValues);
  const maxVal = Math.max(...numericValues);

  function fillFor(zoneId: string): string {
    const v = zoneValues[zoneId];
    if (v === null || minVal === maxVal) return "var(--color-institutional)";
    const t = (v - minVal) / (maxVal - minVal); // 0..1
    // Interpolate between a lighter and darker institutional navy so a
    // higher CPI reads as visually "heavier" - consistent, legible signal.
    const lightness = 55 - t * 25; // 55% (lighter) -> 30% (darker)
    return `hsl(209, 45%, ${lightness}%)`;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-auto max-w-sm"
      role="img"
      aria-label="Map of the Philippines split into NCR and AONCR zones, colored by consumer price index"
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
            tabIndex={0}
            role="button"
            aria-pressed={isSelected}
            aria-label={`${feature.properties.zone_label}, latest CPI ${zoneValues[zoneId]?.toFixed(1) ?? "unavailable"}`}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onSelectZone(zoneId);
            }}
          />
        );
      })}
    </svg>
  );
}