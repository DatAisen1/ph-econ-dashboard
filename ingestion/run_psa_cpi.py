"""
Entry point: run the PSA CPI dlt pipeline and land data into the SAME
warehouse.duckdb that World Bank data lives in (dataset raw_psa, alongside
raw_wb).

Usage:
    python ingestion/run_psa_cpi.py

Makes exactly ONE HTTP request (well under PSA's 10-req/10s limit), so the
rate limiter in psa_http_client.py won't even need to pause here - it
matters once this pipeline calls the API repeatedly (e.g. multiple tables,
or retries), not for this single call.
"""

import pathlib
import time
import dlt
from psa_cpi_source import psa_cpi_source

# Same computation, same file, as ingestion/run_worldbank.py - see that
# file's long comment for why this must be absolute and anchored to this
# file's own location rather than the current working directory.
WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent / "warehouse.duckdb"


def main():
    print(f"Warehouse file: {WAREHOUSE_PATH}")
    pipeline = dlt.pipeline(
        pipeline_name="psa",
        destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
        dataset_name="raw_psa",
    )

    start = time.perf_counter()
    load_info = pipeline.run(psa_cpi_source())
    elapsed = time.perf_counter() - start

    print(load_info)
    print(f"\n--- Elapsed: {elapsed:.2f}s ---")
    print("--- Schema / row counts ---")
    with pipeline.sql_client() as client:
        count = client.execute_sql("SELECT COUNT(*) FROM raw_psa.cpi_observations")
        print(f"cpi_observations: {count[0][0]} rows")

        geo_count = client.execute_sql(
            "SELECT COUNT(DISTINCT geolocation_name) FROM raw_psa.cpi_observations"
        )[0][0]
        commodity_count = client.execute_sql(
            "SELECT COUNT(DISTINCT commodity_name) FROM raw_psa.cpi_observations"
        )[0][0]
        print(f"  {geo_count} distinct geolocations, {commodity_count} distinct commodities")

        # Full per-geolocation breakdown got noisy once we expanded past 3
        # zones (19 x 14 = 266 groups) - a spot-check sample is more useful
        # here than dumping every row.
        print("  Sample geolocations:")
        sample = client.execute_sql(
            "SELECT DISTINCT geolocation_name FROM raw_psa.cpi_observations "
            "ORDER BY geolocation_name LIMIT 5"
        )
        for (name,) in sample:
            print(f"    - {name}")


if __name__ == "__main__":
    main()