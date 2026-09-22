import countryData from "../../../public/data/country_comparison.json";
import metadata from "../../../public/data/metadata.json";
import SiteHeader from "@/components/SiteHeader";
import CompareView from "@/components/CompareView";
import DataProvenance from "@/components/DataProvenance";
import LastUpdated from "@/components/LastUpdated";
import type { CountryComparisonData, ExportMetadata } from "@/lib/types";

const data = countryData as CountryComparisonData;
const meta = metadata as ExportMetadata;
const latestYear = Math.max(
  ...Object.values(data).flatMap((indicator) => indicator.series.map((row) => row.year)),
);

export default function ComparePage() {
  return (
    <>
      <SiteHeader />
      <main className="min-h-screen px-6 py-12 md:px-16 md:py-20 max-w-6xl mx-auto">
        <p className="font-mono text-xs text-muted tracking-wide mb-4">
          World Bank Open Data &middot; Macroeconomic Comparison
        </p>
        <h1 className="font-display text-4xl md:text-5xl leading-tight mb-4 max-w-2xl">
          How does the Philippines compare to its ASEAN peers?
        </h1>
        <div className="mb-10">
          <LastUpdated isoTimestamp={meta.exported_at_utc} />
        </div>

        <CompareView data={data} />
        <DataProvenance
          source="World Bank Open Data"
          sourceUrl="https://data.worldbank.org"
          dataset="Macroeconomic indicators"
          frequency="Annual"
          latestObservation={String(latestYear)}
          refreshedAt={meta.exported_at_utc}
        />
      </main>
    </>
  );
}