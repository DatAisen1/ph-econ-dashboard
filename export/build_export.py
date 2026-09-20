"""
Reads the dbt-built fact tables from warehouse.duckdb and writes static
JSON files into web/public/data/, which the Next.js frontend fetches
directly - no live database, no API server, just files. Matches the
actual update cadence of this data (once a day via the Dagster schedule),
same "don't run infrastructure a problem doesn't need" principle as every
other tool choice in this project.

Usage:
    python export/build_export.py
"""

import json
import pathlib
import datetime
import duckdb

from transform_export import build_ph_detail_json, build_country_comparison_json

WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent / "warehouse.duckdb"
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "web" / "public" / "data"


def main():
    print(f"Warehouse file: {WAREHOUSE_PATH}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)

    ph_detail_raw = con.execute(
        "SELECT geolocation_name, year, period_num, cpi_value FROM main.fact_ph_detail"
    ).df()
    country_raw = con.execute(
        "SELECT country_code, indicator_code, indicator_name, year, value "
        "FROM main.fact_country_comparison"
    ).df()
    con.close()

    ph_detail_json = build_ph_detail_json(ph_detail_raw)
    country_json = build_country_comparison_json(country_raw)

    ph_detail_path = OUTPUT_DIR / "ph_detail.json"
    country_path = OUTPUT_DIR / "country_comparison.json"
    metadata_path = OUTPUT_DIR / "metadata.json"

    ph_detail_path.write_text(json.dumps(ph_detail_json, indent=2))
    country_path.write_text(json.dumps(country_json, indent=2))

    # Last-updated metadata: the frontend needs an honest answer to "when
    # was this refreshed", since this is a static export, not a live
    # database - the page itself has no way to know that on its own.
    metadata = {
        "exported_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ph_detail_row_count": len(ph_detail_json),
        "country_comparison_indicator_count": len(country_json),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(f"Wrote {len(ph_detail_json)} rows to {ph_detail_path}")
    print(f"Wrote {len(country_json)} indicators to {country_path}")
    print(f"Wrote export metadata to {metadata_path}")


if __name__ == "__main__":
    main()