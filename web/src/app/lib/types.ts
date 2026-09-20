// Mirrors export/transform_export.py's output shapes exactly. Keeping
// these in sync manually (not codegen'd) is a real tradeoff for a
// project this size - if the export script's shape changes, this file
// needs a matching edit. Worth automating with a schema/codegen step if
// this project grows past a student capstone.

export type PhDetailRecord = {
  date: string; // "YYYY-MM"
  PHILIPPINES: number | null;
  "National Capital Region (NCR)": number | null;
  "Areas Outside National Capital Region (AONCR)": number | null;
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

export type ExportMetadata = {
  exported_at_utc: string;
  ph_detail_row_count: number;
  country_comparison_indicator_count: number;
};