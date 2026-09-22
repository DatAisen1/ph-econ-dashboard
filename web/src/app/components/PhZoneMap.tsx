"use client";

import { useMemo } from "react";
import { geoMercator, geoPath } from "d3-geo";
import type { PhDetailRecord, RegionGeoJson } from "@/lib/types";

type RegionFeature = RegionGeoJson["features"][number];

function getLatestValue(data: PhDetailRecord[], columnKey: string): number | null {
  for (let i = data.length - 1; i >= 0; i--) {
    const v = data[i][columnKey];
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
  geojson: RegionGeoJson;
  phDetail: PhDetailRecord[];
  selectedZone: string | null; // psa_geolocation_name, or null
  onSelectZone: (psaGeolocationName: string) => void;
}) {
  const width = 400;
  const height = 520;

  const { pathFor, zoneValues } = useMemo(() => {
    const projection = geoMercator().fitSize([width, height], geojson as unknown as GeoJSON.GeoJSON);
    const pathGenerator = geoPath(projection);

    const values: Record<string, number | null> = {};
    for (const f of geojson.features) {
      values[f.properties.psa_geolocation_name] = getLatestValue(
        phDetail,
        f.properties.psa_geolocation_name
      );
    }

    return {
      pathFor: (feature: RegionFeature) => pathGenerator(feature as unknown as GeoJSON.Feature) ?? "",
      zoneValues: values,
    };
  }, [geojson, phDetail]);

  const numericValues = Object.values(zoneValues).filter((v): v is number => v !== null);
  const minVal = Math.min(...numericValues);
  const maxVal = Math.max(...numericValues);

  function fillFor(psaGeolocationName: string): string {
    const v = zoneValues[psaGeolocationName];
    if (v === null || minVal === maxVal) return "var(--color-institutional)";
    const t = (v - minVal) / (maxVal - minVal);
    const lightness = 60 - t * 30; // lighter = lower CPI, darker = higher
    return `hsl(209, 45%, ${lightness}%)`;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-auto max-w-sm"
      role="img"
      aria-label="Map of the Philippines' 18 administrative regions, colored by regional consumer price index"
    >
      {geojson.features.map((feature) => {
        const key = feature.properties.psa_geolocation_name;
        const isSelected = selectedZone === key;
        return (
          <path
            key={key}
            d={pathFor(feature)}
            fill={fillFor(key)}
            stroke="var(--color-surface)"
            strokeWidth={isSelected ? 1.5 : 0.5}
            className="cursor-pointer transition-all duration-150 ease-out hover:opacity-90"
            style={{
              filter: isSelected ? "drop-shadow(0 4px 8px rgba(0,0,0,0.25))" : "none",
            }}
            onClick={() => onSelectZone(key)}
            tabIndex={0}
            role="button"
            aria-pressed={isSelected}
            aria-label={`${feature.properties.zone_id}, latest CPI ${zoneValues[key]?.toFixed(1) ?? "unavailable"}`}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onSelectZone(key);
            }}
          />
        );
      })}
    </svg>
  );
}