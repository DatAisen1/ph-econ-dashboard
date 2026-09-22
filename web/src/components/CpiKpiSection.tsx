"use client";

import { formatDateLabel } from "@/lib/format";
import { getCpiOverviewMetrics } from "@/lib/cpiMetrics";
import type { PhCommodityRecord, PhDetailRecord } from "@/lib/types";

function KpiCard({
  label,
  value,
  unit,
  period,
  comparison,
}: {
  label: string;
  value: string;
  unit: string;
  period: string;
  comparison?: string;
}) {
  return (
    <div className="border border-black/10 bg-surface px-4 py-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="font-mono text-2xl text-institutional mt-2">{value}</p>
      <p className="font-mono text-xs text-muted mt-1">{unit}</p>
      <p className="font-mono text-xs text-muted mt-2">{period}</p>
      {comparison && <p className="font-mono text-xs text-muted mt-1">{comparison}</p>}
    </div>
  );
}

export default function CpiKpiSection({
  phDetail,
  phCommodity,
}: {
  phDetail: PhDetailRecord[];
  phCommodity: PhCommodityRecord[];
}) {
  const { latestDate, nationalCpi, yoy, yoyDate, mom, momDate, foodCpi } = getCpiOverviewMetrics(phDetail, phCommodity);
  const displayDate = latestDate ?? "Unavailable";

  return (
    <section aria-labelledby="overview-kpis" className="mb-14">
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <h2 id="overview-kpis" className="font-display text-xl">What is happening now?</h2>
          <p className="text-sm text-muted mt-2">Latest published national CPI indicators. The period shown is the latest observation available in the export.</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="National CPI"
          value={nationalCpi === null ? "Unavailable" : nationalCpi.toFixed(1)}
          unit="2018 = 100"
          period={displayDate}
        />
        <KpiCard
          label="Year-over-year"
          value={yoy === null ? "Unavailable" : `${yoy.percent >= 0 ? "+" : ""}${yoy.percent.toFixed(1)}%`}
          unit="Annual change in CPI"
          period={yoyDate ? `vs. ${formatDateLabel(yoyDate)}` : "Comparison unavailable"}
        />
        <KpiCard
          label="Month-over-month"
          value={mom === null ? "Unavailable" : `${mom.percent >= 0 ? "+" : ""}${mom.percent.toFixed(1)}%`}
          unit="Monthly change in CPI"
          period={momDate ? `vs. ${formatDateLabel(momDate)}` : "Comparison unavailable"}
        />
        <KpiCard
          label="Food CPI"
          value={foodCpi === null ? "Unavailable" : foodCpi.toFixed(1)}
          unit="2018 = 100"
          period={displayDate}
        />
      </div>
    </section>
  );
}
