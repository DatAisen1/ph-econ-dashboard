// Mirrors export/transform_export.py's output shapes exactly. Keeping
// these in sync manually (not codegen'd) is a real tradeoff for a
// project this size - if the export script's shape changes, this file
// needs a matching edit. Worth automating with a schema/codegen step if
// this project grows past a student capstone.

// Now that regional CPI covers 18 regions (not a fixed 2-zone split),
// PhDetailRecord needs an index signature rather than fixed named keys -
// the actual set of region columns is only known at data-load time.
// "date" is the one guaranteed key; everything else is a region name to
// a CPI value (or null for unpublished months).
export type PhDetailRecord = {
  date: string; // "YYYY-MM"
  [regionName: string]: string | number | null;
};

export type PhCommodityRecord = {
  date: string;
  geolocation_name: string;
  [commodityName: string]: string | number | null;
};

export type CountryComparisonIndicator = {
  indicator_name: string;
  series: CountryComparisonRow[];
};

export type CountryComparisonRow = {
  year: number;
  [countryCode: string]: number | string | null;
};

export type CountryComparisonData = Record<string, CountryComparisonIndicator>;

export type RegionGeoJson = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    properties: { zone_id: string; psa_geolocation_name: string; adm1_pcode: string };
    geometry: GeoJSON.Geometry;
  }[];
};

export type ExportMetadata = {
  exported_at_utc: string;
  ph_detail_row_count: number;
  ph_commodity_row_count?: number;
  country_comparison_indicator_count: number;
};