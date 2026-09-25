"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { MapMetric } from "./PhZoneMap";

export type DashboardFiltersValue = {
  availablePeriods: string[];
  selectedPeriod: string;
  selectedRegion: string | null;
  metric: MapMetric;
  setSelectedPeriod: (period: string) => void;
  setSelectedRegion: (region: string | null) => void;
  setMetric: (metric: MapMetric) => void;
  resetFilters: () => void;
};

const DashboardFiltersContext = createContext<DashboardFiltersValue | null>(null);

export function DashboardFiltersProvider({
  availablePeriods,
  children,
}: {
  availablePeriods: string[];
  children: React.ReactNode;
}) {
  const latestPeriod = availablePeriods.at(-1) ?? "";
  const [selectedPeriod, setSelectedPeriod] = useState(latestPeriod);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [metric, setMetric] = useState<MapMetric>("index");

  const value = useMemo(
    () => ({
      availablePeriods,
      selectedPeriod,
      selectedRegion,
      metric,
      setSelectedPeriod,
      setSelectedRegion,
      setMetric,
      resetFilters: () => {
        setSelectedPeriod(latestPeriod);
        setSelectedRegion(null);
        setMetric("index");
      },
    }),
    [availablePeriods, latestPeriod, metric, selectedPeriod, selectedRegion],
  );

  return <DashboardFiltersContext.Provider value={value}>{children}</DashboardFiltersContext.Provider>;
}

export function useDashboardFilters(): DashboardFiltersValue {
  const context = useContext(DashboardFiltersContext);
  if (!context) throw new Error("useDashboardFilters must be used within DashboardFiltersProvider");
  return context;
}
