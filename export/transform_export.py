"""
Reshapes the warehouse's long/tidy fact tables into the WIDE shape the
frontend actually wants to consume.

This is a real, worth-naming design decision: fact_ph_detail and
fact_country_comparison are correctly modeled as long/tidy tables in the
warehouse (one row per observation) - that's proper dimensional modeling,
good for SQL joins and aggregation. But Recharts (and most charting
libraries) want WIDE data for a multi-line chart: one row per x-axis point
(date/year), one column per series (geolocation/country). Pivoting
long-to-wide at the export boundary, rather than in the warehouse itself,
keeps the warehouse's shape correct for its own purposes while still
serving the frontend what it needs - the warehouse doesn't have to
compromise its modeling for one consumer's convenience.

Pure functions here, no I/O - same split as staging/transform.py, so this
is testable against fixtures without touching DuckDB or the filesystem.
"""

import re
import pandas as pd


def _normalize_geolocation_name(raw_name: str) -> str:
    """
    PXWeb's own labels carry leading dots as a hierarchy-depth indicator
    (".." for region-level, "...." for province-level - we saw this in the
    Phase 1 metadata discovery). That's meaningful in PSA's own UI, but
    it's noise once the label becomes a JSON/JS object key for the
    frontend - "..National Capital Region (NCR)" is an awkward, easy-to-
    typo property name. Strip it here, once, at the export boundary,
    rather than making every downstream consumer re-clean it.
    """
    return re.sub(r"^\.+", "", raw_name).strip()


def _records_with_null_safe_nan(wide: pd.DataFrame) -> list[dict]:
    """
    df.where(pd.notna(df), None) looks like it should turn NaN into None,
    but on a float64 column pandas silently coerces None back to NaN -
    a well-known pandas dtype gotcha. The value never actually becomes
    Python's None, so json.dumps would emit `NaN` (invalid JSON) instead
    of `null`. Converting record-by-record with an explicit pd.isna check
    sidesteps the dtype coercion entirely.
    """
    records = wide.to_dict(orient="records")
    return [
        {k: (None if pd.isna(v) else v) for k, v in record.items()}
        for record in records
    ]


def build_ph_detail_json(df: pd.DataFrame) -> list[dict]:
    """
    Input: long rows with geolocation_name, year, period_num, cpi_value.
    Output: wide records like {"date": "2018-01", "PHILIPPINES": 97.2, ...},
    sorted chronologically - exactly what a Recharts <LineChart> wants.
    """
    working = df.copy()
    working["geolocation_name"] = working["geolocation_name"].apply(_normalize_geolocation_name)
    working["date"] = working["year"].astype(str) + "-" + working["period_num"].astype(str).str.zfill(2)

    # Defensive check: this function assumes exactly ONE row per
    # (date, geolocation) - i.e. the caller has already filtered to a
    # single commodity. If that assumption breaks (e.g. someone expands
    # scope upstream and forgets to filter, exactly as happened once
    # already in this project), pivot_table's aggfunc="first" would
    # silently pick an arbitrary value instead of erroring. Catch it here
    # instead of shipping wrong numbers to the site.
    duplicate_check = working.groupby(["date", "geolocation_name"]).size()
    if (duplicate_check > 1).any():
        bad = duplicate_check[duplicate_check > 1].index[0]
        raise ValueError(
            f"Expected exactly one row per (date, geolocation), but found "
            f"{duplicate_check.max()} for {bad}. Did the caller forget to "
            f"filter to a single commodity before calling this function?"
        )

    wide = working.pivot_table(
        index="date", columns="geolocation_name", values="cpi_value", aggfunc="first"
    )
    wide = wide.sort_index().reset_index()

    # NaN (missing months) must survive as JSON null, not be dropped or
    # coerced to 0 - a 0 would look like deflation to zero, which is a
    # meaningfully different (and wrong) claim than "no data yet".
    return _records_with_null_safe_nan(wide)


def build_ph_commodity_json(df: pd.DataFrame) -> list[dict]:
    """Build one wide record per month and geography for CPI commodities."""
    working = df.copy()
    working["geolocation_name"] = working["geolocation_name"].apply(_normalize_geolocation_name)
    working["date"] = working["year"].astype(str) + "-" + working["period_num"].astype(str).str.zfill(2)

    duplicate_check = working.groupby(["date", "geolocation_name", "commodity_name"]).size()
    if (duplicate_check > 1).any():
        bad = duplicate_check[duplicate_check > 1].index[0]
        raise ValueError(
            f"Expected exactly one row per (date, geolocation, commodity), but found "
            f"{duplicate_check.max()} for {bad}."
        )

    wide = working.pivot_table(
        index=["date", "geolocation_name"],
        columns="commodity_name",
        values="cpi_value",
        aggfunc="first",
    ).reset_index()
    wide = wide.sort_values(["date", "geolocation_name"])
    return _records_with_null_safe_nan(wide)


def build_country_comparison_json(df: pd.DataFrame) -> dict:
    """
    Input: long rows with country_code, indicator_code, indicator_name,
    year, value.
    Output: {indicator_code: {indicator_name, series: [{year, PHL: v, ...}]}}
    - one wide time series per indicator, grouped so the frontend can pick
    an indicator and get a ready-to-chart series.
    """
    result = {}
    for indicator_code, group in df.groupby("indicator_code"):
        indicator_name = group["indicator_name"].iloc[0]
        wide = group.pivot_table(
            index="year", columns="country_code", values="value", aggfunc="first"
        )
        wide = wide.sort_index().reset_index()
        series = _records_with_null_safe_nan(wide)
        result[indicator_code] = {
            "indicator_name": indicator_name,
            "series": series,
        }
    return result