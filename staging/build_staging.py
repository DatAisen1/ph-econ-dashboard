"""
Reads raw_wb.wb_observations from the warehouse DuckDB, applies the staging
transform, and writes typed, dimension-enriched Parquet to staging/output/.

Usage:
    python staging/build_staging.py
"""

import pathlib
import duckdb
import pandas as pd

from transform import clean_observations, enrich_with_country_dim

WAREHOUSE_DB = pathlib.Path(__file__).resolve().parent.parent / "warehouse.duckdb"
SEED_PATH = pathlib.Path(__file__).parent.parent / "seeds" / "dim_country.csv"
OUTPUT_DIR = pathlib.Path(__file__).parent / "output"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    con = duckdb.connect(str(WAREHOUSE_DB), read_only=True)
    raw = con.execute("SELECT * FROM raw_wb.wb_observations").df()
    con.close()

    dim_country = pd.read_csv(SEED_PATH)

    staged = clean_observations(raw)
    enriched = enrich_with_country_dim(staged, dim_country)

    # Surface data-quality problems NOW, at staging, rather than letting
    # them silently reach the warehouse. This is the pandas-level version
    # of what a dbt not_null/relationship test will do more formally in
    # Phase 3 - the check matters more than which tool runs it.
    missing_region = enriched[enriched["region"].isna()]
    if not missing_region.empty:
        unknown_countries = missing_region["country_code"].unique().tolist()
        print(
            f"WARNING: {len(missing_region)} rows have no country_dim match "
            f"for countries {unknown_countries}. Update seeds/dim_country.csv."
        )

    dim_country.to_parquet(OUTPUT_DIR / "dim_country.parquet", index=False)
    enriched.to_parquet(OUTPUT_DIR / "stg_wb_observations.parquet", index=False)

    print(f"Wrote {len(dim_country)} rows to dim_country.parquet")
    print(f"Wrote {len(enriched)} rows to stg_wb_observations.parquet")
    print(f"\nSchema:\n{enriched.dtypes}")


if __name__ == "__main__":
    main()