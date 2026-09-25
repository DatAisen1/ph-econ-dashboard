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
  explanation,
}: {
  label: string;
  value: string;
  unit: string;
  period: string;
  comparison?: string;
  explanation?: string;
}) {
  return (
    <div className="border border-black/10 bg-surface px-4 py-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="font-mono text-2xl text-institutional mt-2">{value}</p>
      <p className="font-mono text-xs text-muted mt-1">{unit}</p>
      <p className="font-mono text-xs text-muted mt-2">{period}</p>
      {comparison && <p className="font-mono text-xs text-muted mt-1">{comparison}</p>}
      {explanation && <p className="text-xs text-muted leading-relaxed mt-3">{explanation}</p>}
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
  const { latestDate, nationalCpi, yoy, yoyDate, mom, momDate, foodCpi, nationalPrevious, nationalPreviousDate, yoyPrevious, momPrevious, foodPrevious } = getCpiOverviewMetrics(phDetail, phCommodity);
  const displayDate = latestDate ?? "Unavailable";
  const signed = (value: number, suffix = "%") => `${value >= 0 ? "+" : ""}${value.toFixed(1)}${suffix}`;

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
          comparison={nationalPrevious === null || nationalPreviousDate === null ? "Previous: Not available" : `Previous: ${nationalPrevious.toFixed(1)} (${formatDateLabel(nationalPreviousDate)})`}
          explanation="The CPI index tracks the price of a household basket relative to 2018."
        />
        <KpiCard
          label="Year-over-year"
          value={yoy === null ? "Unavailable" : `${yoy.percent >= 0 ? "+" : ""}${yoy.percent.toFixed(1)}%`}
          unit="Annual change in CPI"
          period={yoyDate ? `vs. ${formatDateLabel(yoyDate)}` : "Comparison unavailable"}
          comparison={yoy === null || yoyPrevious === null ? "Previous YoY: Not available" : `Previous YoY: ${signed(yoyPrevious.percent)} · Δ ${signed(yoy.percent - yoyPrevious.percent, " pp")}`}
          explanation="YoY compares this month with the same month one year earlier."
        />
        <KpiCard
          label="Month-over-month"
          value={mom === null ? "Unavailable" : `${mom.percent >= 0 ? "+" : ""}${mom.percent.toFixed(1)}%`}
          unit="Monthly change in CPI"
          period={momDate ? `vs. ${formatDateLabel(momDate)}` : "Comparison unavailable"}
          comparison={mom === null || momPrevious === null ? "Previous MoM: Not available" : `Previous MoM: ${signed(momPrevious.percent)} · Δ ${signed(mom.percent - momPrevious.percent, " pp")}`}
          explanation="MoM compares this month with the immediately previous month."
        />
        <KpiCard
          label="Food CPI"
          value={foodCpi === null ? "Unavailable" : foodCpi.toFixed(1)}
          unit="2018 = 100"
          period={displayDate}
          comparison={foodPrevious === null || nationalPreviousDate === null ? "Previous: Not available" : `Previous: ${foodPrevious.toFixed(1)} (${formatDateLabel(nationalPreviousDate)})`}
          explanation="Food CPI tracks price changes for food and non-alcoholic beverages."
        />
      </div>
    </section>
  );
}
