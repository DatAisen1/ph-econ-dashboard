"""
Staging transform for World Bank observations: raw dlt/DuckDB table -> typed,
dimension-enriched Parquet.

Deliberately split from build_staging.py: the functions here take and return
DataFrames only, with no database or filesystem calls. That's what makes
test_staging.py possible without a live DuckDB connection - a pattern worth
keeping as pipelines grow, because "transform logic mixed with I/O" is one
of the most common reasons ETL code becomes untestable.
"""

import pandas as pd


def clean_observations(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Type-cast and lightly rename raw wb_observations rows.

    Rule from Phase 3 planning, applied here too: staging renames/casts
    only. No joins, no business logic - that belongs one layer up.
    """
    df = raw.copy()
    df["year"] = df["year"].astype("int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # preserves NaN, doesn't crash on it
    df["country_code"] = df["country_code"].astype("string")
    df["indicator_code"] = df["indicator_code"].astype("string")
    return df[["country_code", "indicator_code", "indicator_name", "year", "value"]]


def enrich_with_country_dim(staged: pd.DataFrame, dim_country: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join staged observations onto the country dimension.

    LEFT join, not inner: if a country appears in the API response that
    ISN'T in our seed yet (e.g. we later add MYS to run_worldbank.py and
    forget to update the seed), we want that row to survive with a null
    region/income_group - visibly wrong and easy to catch in a dbt test -
    rather than silently disappearing from an inner join, which is a much
    worse failure mode: less data, no error, nothing to notice.
    """
    return staged.merge(dim_country, on="country_code", how="left")