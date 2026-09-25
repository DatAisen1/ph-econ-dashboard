import phDetailData from "../../public/data/ph_detail.json";
import regionsGeoJson from "../../public/data/ph_regions.json";
import phCommodityData from "../../public/data/ph_commodity.json";
import metadata from "../../public/data/metadata.json";
import SiteHeader from "@/components/SiteHeader";
import DashboardExperience from "@/components/DashboardExperience";
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
  return (
    <>
      <SiteHeader />
      <main className="min-h-screen px-6 py-12 md:px-16 md:py-20 max-w-6xl mx-auto">
        <DashboardExperience
          phDetail={phDetail}
          phCommodity={phCommodity}
          regions={regions}
          metadata={meta}
        />
      </main>
    </>
  );
}