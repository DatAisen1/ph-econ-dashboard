import phDetailData from "../../public/data/ph_detail.json";
import regionsGeoJson from "../../public/data/ph_regions.json";
import phCommodityData from "../../public/data/ph_commodity.json";
import metadata from "../../public/data/metadata.json";
import SiteHeader from "@/components/SiteHeader";
import DashboardHero from "@/components/DashboardHero";
import DataProvenance from "@/components/DataProvenance";
import KeyTakeaways from "@/components/KeyTakeaways";
import LastUpdated from "@/components/LastUpdated";
import { getCpiOverviewMetrics } from "@/lib/cpiMetrics";
import type {
  ExportMetadata,
  PhCommodityRecord,
  PhDetailRecord,
  RegionGeoJson,
} from "@/lib/types";

const phDetail = phDetailData as PhDetailRecord[];
const phCommodity = phCommodityData as PhCommodityRecord[];
const meta = metadata as ExportMetadata;
const regions = regionsGeoJson as unknown as RegionGeoJson;

export default function Home() {
  const metrics = getCpiOverviewMetrics(phDetail, phCommodity);

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen px-6 py-12 md:px-16 md:py-20 max-w-6xl mx-auto">
        <div className="mb-6">
          <LastUpdated isoTimestamp={meta.exported_at_utc} />
        </div>

        {metrics.latestDate && metrics.nationalCpi !== null ? (
          <>
            <DashboardHero
              phDetail={phDetail}
              phCommodity={phCommodity}
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
            />
            <DataProvenance
              source="Philippine Statistics Authority OpenSTAT"
              sourceUrl="https://openstat.psa.gov.ph"
              dataset="Consumer Price Index"
              frequency="Monthly"
              basePeriod="2018 = 100"
              latestObservation={metrics.latestDate}
              refreshedAt={meta.exported_at_utc}
            />
          </>
        ) : (
          <p className="text-muted">No published CPI data available yet.</p>
        )}
      </main>
    </>
  );
}