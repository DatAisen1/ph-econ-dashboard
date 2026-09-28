"""
Runner for the PSA Weights dlt pipeline.

Usage:
    python ingestion/run_psa_weights.py
"""

import pathlib
import sys

# Make ingestion/ importable for the dlt source
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import dlt
from psa_weights_source import psa_weights_source

# Same file the Dagster asset and other scripts use - absolute path anchored
# to this file's location, not CWD-fragile like the old bare string bug.
WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent / "warehouse.duckdb"


def main():
    print(f"Warehouse file: {WAREHOUSE_PATH}")

    pipeline = dlt.pipeline(
        pipeline_name="psa_weights",
        destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
        dataset_name="raw_psa",
    )
    load_info = pipeline.run(psa_weights_source())
    print(load_info)

    with pipeline.sql_client() as client:
        row_count = client.execute_sql(
            "SELECT COUNT(*) FROM raw_psa.cpi_weights"
        )[0][0]
        print(f"Loaded {row_count} rows into raw_psa.cpi_weights")


if __name__ == "__main__":
    main()
