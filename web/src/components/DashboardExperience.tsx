"use client";

import { useMemo } from "react";
import CpiKpiSection from "./CpiKpiSection";
import CpiUnderstanding from "./CpiUnderstanding";
import DashboardHero from "./DashboardHero";
import DataProvenance from "./DataProvenance";
import KeyTakeaways from "./KeyTakeaways";
import LastUpdated from "./LastUpdated";
import { DashboardFiltersProvider, useDashboardFilters } from "./DashboardFilters";
import { getCpiOverviewMetrics } from "@/lib/cpiMetrics";
import { formatDateLabel } from "@/lib/format";
import type { ExportMetadata, PhCommodityRecord, PhDetailRecord, RegionGeoJson } from "@/lib/types";

function MonthlyDashboard({
  phDetail,
  phCommodity,
  regions,
  metadata,
}: {
  phDetail: PhDetailRecord[];
  phCommodity: PhCommodityRecord[];
  regions: RegionGeoJson;
  metadata: ExportMetadata;
}) {
  const { availablePeriods, selectedPeriod, setSelectedPeriod, resetFilters } = useDashboardFilters();
  const selectedDetail = useMemo(
    () => phDetail.filter((row) => row.date <= selectedPeriod),
    [phDetail, selectedPeriod],
  );
  const selectedCommodity = useMemo(
    () => phCommodity.filter((row) => row.date <= selectedPeriod),
    [phCommodity, selectedPeriod],
  );
  const metrics = useMemo(
    () => getCpiOverviewMetrics(selectedDetail, selectedCommodity, selectedPeriod),
    [selectedCommodity, selectedDetail, selectedPeriod],
  );
  const periodLabel = selectedPeriod ? formatDateLabel(selectedPeriod) : "Unavailable";

  return (
    <>
      <div className="mb-6">
        <LastUpdated isoTimestamp={metadata.exported_at_utc} />
      </div>
      <div className="flex flex-wrap items-end justify-between gap-4 border-y border-black/10 py-4 mb-10">
        <label className="flex flex-col gap-2 text-sm">
          <span className="font-mono text-xs text-muted uppercase tracking-wide">Period</span>
          <select
            value={selectedPeriod}
            onChange={(event) => setSelectedPeriod(event.target.value)}
            className="border border-black/15 bg-surface px-3 py-2 text-sm text-ink"
            aria-label="Select dashboard period"
          >
            {availablePeriods.map((period) => (
              <option key={period} value={period}>{formatDateLabel(period)}</option>
            ))}
          </select>
        </label>
        <div className="flex items-center gap-4">
          <p className="font-mono text-xs text-muted">Showing {periodLabel}</p>
          <button type="button" onClick={resetFilters} className="text-xs font-mono text-muted border border-black/15 px-3 py-2 hover:border-institutional">
            Reset filters
          </button>
        </div>
      </div>

      {metrics.latestDate && metrics.nationalCpi !== null ? (
        <>
          <CpiKpiSection phDetail={selectedDetail} phCommodity={selectedCommodity} />
          <CpiUnderstanding latestValue={metrics.nationalCpi} latestDate={metrics.latestDate} />
          <DashboardHero
            phDetail={selectedDetail}
            phCommodity={selectedCommodity}
            geojson={regions}
            latestDate={metrics.latestDate}
            latestNational={metrics.nationalCpi}
            momChange={metrics.mom}
            yoyChange={metrics.yoy}
          />
          <KeyTakeaways
            latestDate={metrics.latestDate}
            nationalCpi={metrics.nationalCpi}
            yoyPercent={metrics.yoy?.percent ?? null}
            yoyDate={metrics.yoyDate}
            momPercent={metrics.mom?.percent ?? null}
            momDate={metrics.momDate}
            foodCpi={metrics.foodCpi}
            phDetail={selectedDetail}
            phCommodity={selectedCommodity}
          />
          <DataProvenance
            source="Philippine Statistics Authority OpenSTAT"
            sourceUrl="https://openstat.psa.gov.ph"
            dataset="Consumer Price Index"
            frequency="Monthly"
            basePeriod="2018 = 100"
            latestObservation={metrics.latestDate}
            refreshedAt={metadata.exported_at_utc}
          />
        </>
      ) : (
        <p className="text-muted">No data is available for {periodLabel}.</p>
      )}
    </>
  );
}

export default function DashboardExperience(props: {
  phDetail: PhDetailRecord[];
  phCommodity: PhCommodityRecord[];
  regions: RegionGeoJson;
  metadata: ExportMetadata;
}) {
  const availablePeriods = [...new Set(props.phDetail.map((row) => row.date))].sort();
  return (
    <DashboardFiltersProvider availablePeriods={availablePeriods}>
      <MonthlyDashboard {...props} />
    </DashboardFiltersProvider>
  );
}
