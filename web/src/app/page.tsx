import phDetailData from "../../public/data/ph_detail.json";
import zonesGeoJson from "../../public/data/ph_zones.json";
import metadata from "../../public/data/metadata.json";
import SiteHeader from "@/components/SiteHeader";
import DashboardHero from "@/components/DashboardHero";
import LastUpdated from "@/components/LastUpdated";
import { computeChange } from "@/lib/format";
import type { PhDetailRecord, ExportMetadata } from "@/lib/types";

const phDetail = phDetailData as PhDetailRecord[];
const meta = metadata as ExportMetadata;

function findLatestNationalIndex(data: PhDetailRecord[]): number {
  // Last row isn't guaranteed to have a value - trailing months can be
  // entirely unpublished and get dropped by the export's pivot for OTHER
  // zones while this one still has a gap.
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i].PHILIPPINES !== null) return i;
  }
  return -1;
}

export default function Home() {
  const latestIndex = findLatestNationalIndex(phDetail);
  const latest = latestIndex >= 0 ? phDetail[latestIndex] : null;

  // MoM: the immediately preceding row. YoY: 12 rows back, since this
  // series is monthly - both are simple index arithmetic once we know
  // where "latest" actually is (not just the last array entry).
  const momPrevious = latestIndex >= 1 ? phDetail[latestIndex - 1] : null;
  const yoyPrevious = latestIndex >= 12 ? phDetail[latestIndex - 12] : null;

  const momChange = latest
    ? computeChange(latest.PHILIPPINES, momPrevious?.PHILIPPINES ?? null)
    : null;
  const yoyChange = latest
    ? computeChange(latest.PHILIPPINES, yoyPrevious?.PHILIPPINES ?? null)
    : null;

  return (
    <>
      <SiteHeader />
      <main className="min-h-screen px-6 py-12 md:px-16 md:py-20 max-w-6xl mx-auto">
        <div className="mb-6">
          <LastUpdated isoTimestamp={meta.exported_at_utc} />
        </div>

        {latest && latest.PHILIPPINES !== null ? (
          <DashboardHero
            phDetail={phDetail}
            geojson={zonesGeoJson}
            latestDate={latest.date}
            latestNational={latest.PHILIPPINES}
            momChange={momChange}
            yoyChange={yoyChange}
          />
        ) : (
          <p className="text-muted">No published CPI data available yet.</p>
        )}
      </main>
    </>
  );
}