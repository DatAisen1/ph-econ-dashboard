"""
Entry point: run the World Bank dlt pipeline and land data into DuckDB.

Usage (from anywhere - the warehouse path no longer depends on your
current working directory):
    python ingestion/run_worldbank.py
"""

import pathlib
import time
import dlt
from worldbank_source import worldbank_source

# BUG THIS FIXES: dlt.pipeline(destination="duckdb", ...) with a bare string
# creates its file in whatever the CURRENT WORKING DIRECTORY happens to be
# when the code runs - not a fixed location. That was invisible when this
# script was always run from ingestion/, but broke the moment Dagster ran
# the same pipeline logic from orchestration/, silently creating a SECOND,
# separate database file instead of writing to the one dbt was reading.
#
# Fix: compute one absolute path, anchored to this file's own location on
# disk (not to whatever folder the terminal happens to be in), so every
# caller - this script, the Dagster asset, dbt - agrees on the same file
# regardless of where the process was launched from.
WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent / "warehouse.duckdb"

COUNTRIES = ["PHL", "IDN", "THA", "VNM", "KOR"]

INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_annual_pct",
    "FP.CPI.TOTL.ZG": "inflation_cpi_annual_pct",
    "SL.UEM.TOTL.ZS": "unemployment_pct_of_labor_force",
    "NY.GDP.PCAP.KD": "gdp_per_capita_constant_usd",
}


def main():
    print(f"Warehouse file: {WAREHOUSE_PATH}")
    pipeline = dlt.pipeline(
        pipeline_name="worldbank",
        destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
        dataset_name="raw_wb",
    )

    start = time.perf_counter()
    load_info = pipeline.run(
        worldbank_source(countries=COUNTRIES, indicators=INDICATORS)
    )
    elapsed = time.perf_counter() - start

    print(load_info)
    print(f"\n--- Elapsed: {elapsed:.2f}s ---")
    print("--- Schema / row counts ---")
    with pipeline.sql_client() as client:
        count = client.execute_sql("SELECT COUNT(*) FROM raw_wb.wb_observations")
        print(f"wb_observations: {count[0][0]} rows")
        by_indicator = client.execute_sql(
            "SELECT indicator_code, COUNT(*) FROM raw_wb.wb_observations "
            "GROUP BY indicator_code ORDER BY indicator_code"
        )
        for indicator_code, n in by_indicator:
            print(f"  {indicator_code}: {n} rows")


if __name__ == "__main__":
    main()