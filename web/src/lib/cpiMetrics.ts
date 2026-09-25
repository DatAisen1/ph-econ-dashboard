import { computeChange, type ChangeResult } from "@/lib/format";
import type { PhCommodityRecord, PhDetailRecord } from "@/lib/types";

export const FOOD_COMMODITY_KEY = "01 - FOOD AND NON-ALCOHOLIC BEVERAGES";

export type CpiOverviewMetrics = {
  latestDate: string | null;
  nationalCpi: number | null;
  yoy: ChangeResult | null;
  yoyDate: string | null;
  mom: ChangeResult | null;
  momDate: string | null;
  foodCpi: number | null;
  nationalPrevious: number | null;
  nationalPreviousDate: string | null;
  yoyPrevious: ChangeResult | null;
  momPrevious: ChangeResult | null;
  foodPrevious: number | null;
};

function numeric(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

function latestIndex(data: PhDetailRecord[], key: string): number {
  for (let index = data.length - 1; index >= 0; index -= 1) {
    if (numeric(data[index][key]) !== null) return index;
  }
  return -1;
}

function periodIndex(data: PhDetailRecord[], key: string, selectedDate?: string): number {
  if (selectedDate) {
    const index = data.findIndex((row) => row.date === selectedDate && numeric(row[key]) !== null);
    return index;
  }
  return latestIndex(data, key);
}

export function getCpiOverviewMetrics(
  phDetail: PhDetailRecord[],
  phCommodity: PhCommodityRecord[],
  selectedDate?: string,
): CpiOverviewMetrics {
  const index = periodIndex(phDetail, "PHILIPPINES", selectedDate);
  if (index < 0) {
    return { latestDate: null, nationalCpi: null, yoy: null, yoyDate: null, mom: null, momDate: null, foodCpi: null, nationalPrevious: null, nationalPreviousDate: null, yoyPrevious: null, momPrevious: null, foodPrevious: null };
  }

  const latest = phDetail[index];
  const nationalCpi = numeric(latest.PHILIPPINES);
  const previousMonth = index >= 1 ? phDetail[index - 1] : null;
  const twoMonthsAgo = index >= 2 ? phDetail[index - 2] : null;
  const previousYear = index >= 12 ? phDetail[index - 12] : null;
  const previousYearBefore = index >= 24 ? phDetail[index - 24] : null;
  const foodRow = phCommodity.find(
    (row) => row.date === latest.date && row.geolocation_name === "PHILIPPINES",
  );
  const previousFoodRow = previousMonth
    ? phCommodity.find((row) => row.date === previousMonth.date && row.geolocation_name === "PHILIPPINES")
    : undefined;

  return {
    latestDate: latest.date,
    nationalCpi,
    yoy: computeChange(nationalCpi, numeric(previousYear?.PHILIPPINES)),
    yoyDate: previousYear?.date ?? null,
    mom: computeChange(nationalCpi, numeric(previousMonth?.PHILIPPINES)),
    momDate: previousMonth?.date ?? null,
    foodCpi: numeric(foodRow?.[FOOD_COMMODITY_KEY]),
    nationalPrevious: numeric(previousMonth?.PHILIPPINES),
    nationalPreviousDate: previousMonth?.date ?? null,
    yoyPrevious: computeChange(numeric(previousYear?.PHILIPPINES), numeric(previousYearBefore?.PHILIPPINES)),
    momPrevious: computeChange(numeric(previousMonth?.PHILIPPINES), numeric(twoMonthsAgo?.PHILIPPINES)),
    foodPrevious: numeric(previousFoodRow?.[FOOD_COMMODITY_KEY]),
  };
}
