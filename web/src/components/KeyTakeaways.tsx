import { formatDateLabel } from "@/lib/format";
import type { PhCommodityRecord, PhDetailRecord } from "@/lib/types";
import { useDashboardFilters } from "./DashboardFilters";

const FOOD_KEY = "01 - FOOD AND NON-ALCOHOLIC BEVERAGES";

function numeric(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

export default function KeyTakeaways({
  latestDate,
  nationalCpi,
  yoyPercent,
  yoyDate,
  momPercent,
  momDate,
  foodCpi,
  phDetail,
  phCommodity,
}: {
  latestDate: string;
  nationalCpi: number;
  yoyPercent: number | null;
  yoyDate: string | null;
  momPercent: number | null;
  momDate: string | null;
  foodCpi: number | null;
  phDetail: PhDetailRecord[];
  phCommodity: PhCommodityRecord[];
}) {
  const { selectedRegion } = useDashboardFilters();
  const latestDetail = phDetail.at(-1);
  const regionRows = latestDetail
    ? Object.entries(latestDetail)
        .filter(([region, value]) => region !== "date" && region !== "PHILIPPINES" && numeric(value) !== null)
        .map(([region, value]) => ({ region, value: numeric(value) as number }))
        .sort((a, b) => b.value - a.value)
    : [];
  const selectedRegionRow = selectedRegion
    ? regionRows.find((row) => row.region === selectedRegion)
    : null;
  const latestCommodityRows = phCommodity.filter(
    (row) => row.date === latestDate && row.geolocation_name === "PHILIPPINES",
  );
  const foodRow = latestCommodityRows[0];
  const foodValue = numeric(foodRow?.[FOOD_KEY]);
  const takeaways = [
    `National CPI was ${nationalCpi.toFixed(1)} in ${formatDateLabel(latestDate)}, measured against a 2018 base of 100.`,
    yoyPercent === null || yoyDate === null
      ? null
      : `National CPI changed ${yoyPercent >= 0 ? "+" : ""}${yoyPercent.toFixed(1)}% year-over-year versus ${formatDateLabel(yoyDate)}.`,
    momPercent === null || momDate === null
      ? null
      : `National CPI changed ${momPercent >= 0 ? "+" : ""}${momPercent.toFixed(1)}% month-over-month versus ${formatDateLabel(momDate)}.`,
    foodCpi === null ? null : `Food CPI was ${foodCpi.toFixed(1)} in ${formatDateLabel(latestDate)}, using the same 2018 base.`,
    selectedRegionRow == null
      ? regionRows[0] === undefined ? null : `${regionRows[0].region} recorded the highest regional CPI index at ${regionRows[0].value.toFixed(1)} for ${formatDateLabel(latestDate)}.`
      : `${selectedRegionRow.region} recorded a CPI index of ${selectedRegionRow.value.toFixed(1)} for ${formatDateLabel(latestDate)}.`,
    foodValue === null ? null : `Food and non-alcoholic beverages measured ${foodValue.toFixed(1)} in the selected period; this is an observation, not a causal explanation.`,
  ].filter((takeaway): takeaway is string => takeaway !== null);

  return (
    <section aria-labelledby="key-takeaways" className="mb-16">
      <h2 id="key-takeaways" className="font-display text-xl mb-4">Key takeaways</h2>
      <ul className="grid gap-3 md:grid-cols-2 text-sm text-muted leading-relaxed">
        {takeaways.map((takeaway, index) => <li key={`${index}-${takeaway}`} className="border-l-2 border-signal pl-4">{takeaway}</li>)}
      </ul>
    </section>
  );
}
