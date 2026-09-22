"""
dlt source for PSA OpenSTAT's Consumer Price Index table.

Table: "Consumer Price Index for All Income Households by Commodity Group
(2018=100): January 2018 - August 2026", 0012M4ACP22.px.

FORMAT DECISION: this pipeline originally targeted response format
"json-stat2" (a genuine open standard, safer to parse than PXWeb's
underdocumented plain "json"). Live testing against PSA's actual API
revealed json-stat2 always returns exactly 1 value regardless of query
size - a real defect in this specific deployment (which labels itself
"Alpha Version: 10.2.4.0"), not something we could work around. Verified
via ingestion/diagnose_psa_query.py.

"csv" format was verified separately (diagnose_psa_csv.py) to return
correct, real data. PSA's own official API docs also demonstrate CSV as
their primary worked example - so this is the best-tested path on this
deployment, not just the one that happened to work in one test.

RESPONSE SHAPE: PXWeb's CSV export is a WIDE/PIVOT table, not one row per
cell. Rows = the dimensions we multi-selected as "stubs" (Geolocation,
Commodity Description); columns = one per (Year, Period) combination,
headered like "2018 Jan". We melt this back into long/tidy rows - one per
(geolocation, commodity, year, period) - to match the fact-table shape
the rest of this project uses (same shape as raw_wb.wb_observations).

SCOPE FOR v2 (expanded from v1's 3-geolocation, 1-commodity scope):
  - Geolocation: PHILIPPINES + all 18 top-level regions (confirmed via
    discover_psa_expansion.py against the live API on 2026-09-20).
    AONCR (code "2") is now redundant - it was a stand-in aggregate for
    "everywhere except NCR" before we had real per-region granularity.
    Dropping it: the 18 real regions supersede it, and keeping both would
    double-count AONCR-covered areas alongside their individual regions.
  - Commodity Description: ALL ITEMS + all 13 top-level commodity
    divisions (Food, Transport, Housing, etc.) - NOT the full 354-way
    granular breakdown, which is far more detail than the "which
    commodity groups drive inflation" story needs.
  - Year: all 9 available (2018-2026).
  - Period: the 12 calendar months only, excluding PXWeb's "Ave" row

  Cell count check (PXWeb's own UI warns at 100,000 cells/query):
  19 geolocations x 14 commodities x 9 years x 12 months = 28,728 cells.
  Comfortably under the limit - no need to chunk this into multiple calls.
"""

import io
import pathlib
import datetime

import dlt
import pandas as pd

from psa_http_client import build_session, psa_rate_limiter, PXWEB_BASE

TABLE_PATH = "DB/2M/PI/CPI/2018NEW/0012M4ACP22.px"

# Codes confirmed via discover_psa_expansion.py against the live API.
GEOLOCATION_CODES = [
    "0",    # PHILIPPINES (national)
    "1",    # NCR
    "3",    # CAR
    "11",   # Region I (Ilocos Region)
    "16",   # Region II (Cagayan Valley)
    "22",   # Region III (Central Luzon)
    "32",   # Region IV-A (CALABARZON)
    "39",   # MIMAROPA Region
    "46",   # Region V (Bicol Region)
    "53",   # Region VI (Western Visayas)
    "60",   # Region VII (Central Visayas)
    "66",   # Region VIII (Eastern Visayas)
    "74",   # Region IX (Zamboanga Peninsula)
    "80",   # Region X (Northern Mindanao)
    "88",   # Region XI (Davao Region)
    "95",   # Region XII (SOCCSKSARGEN)
    "101",  # BARMM
    "108",  # Region XIII (Caraga)
    "115",  # Negros Island Region (NIR)
]

COMMODITY_CODES = [
    "0",    # ALL ITEMS
    "1",    # 01 Food and non-alcoholic beverages
    "79",   # 02 Alcoholic beverages and tobacco
    "97",   # 03 Clothing and footwear
    "119",  # 04 Housing, water, electricity, gas, and other fuels
    "141",  # 05 Furnishings, household equipment and routine household maintenance
    "180",  # 06 Health
    "203",  # 07 Transport
    "242",  # 08 Information and communication
    "264",  # 09 Recreation, sport and culture
    "307",  # 10 Education services
    "323",  # 11 Restaurants and accommodation services
    "330",  # 12 Financial services
    "336",  # 13 Personal care, and miscellaneous goods and services
]

YEAR_CODES = [str(i) for i in range(9)]  # 2018..2026
PERIOD_CODES = [str(i) for i in range(12)]  # Jan..Dec, excludes "Ave"

MONTH_ABBR_TO_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

RAW_LANDING_DIR = pathlib.Path(__file__).resolve().parent.parent / "raw" / "psa"

_session = build_session()


def _build_query() -> dict:
    return {
        "query": [
            {"code": "Geolocation", "selection": {"filter": "item", "values": GEOLOCATION_CODES}},
            {"code": "Commodity Description", "selection": {"filter": "item", "values": COMMODITY_CODES}},
            {"code": "Year", "selection": {"filter": "item", "values": YEAR_CODES}},
            {"code": "Period", "selection": {"filter": "item", "values": PERIOD_CODES}},
        ],
        "response": {"format": "csv"},
    }


def _land_raw(csv_text: str) -> pathlib.Path:
    RAW_LANDING_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = RAW_LANDING_DIR / f"cpi_{ts}.csv"
    path.write_text(csv_text)
    return path


def _fetch_cpi_csv() -> str:
    """Isolated so tests can monkeypatch this one function instead of the network."""
    psa_rate_limiter.wait_if_needed()
    resp = _session.post(
        f"{PXWEB_BASE}/{TABLE_PATH}",
        json=_build_query(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.text


def parse_csv_to_records(csv_text: str) -> list[dict]:
    """
    Pure function (no I/O) so it's independently testable against a fixture -
    same split as staging/transform.py's clean_observations().

    Melts PXWeb's wide export (one column per Year+Period) into long rows.
    """
    df = pd.read_csv(io.StringIO(csv_text), na_values=["..", "-", ""])

    label_cols = ["Geolocation", "Commodity Description"]
    data_cols = [c for c in df.columns if c not in label_cols]

    long_df = df.melt(
        id_vars=label_cols,
        value_vars=data_cols,
        var_name="year_period",
        value_name="cpi_value",
    )

    # "2018 Jan" -> year=2018, period="Jan". rsplit handles it even if a
    # geolocation label elsewhere had a stray space - we're splitting the
    # COLUMN HEADER here, not a label column, so this is safe.
    split = long_df["year_period"].str.rsplit(" ", n=1, expand=True)
    long_df["year"] = split[0].astype(int)
    long_df["period_name"] = split[1]
    long_df["period_num"] = long_df["period_name"].map(MONTH_ABBR_TO_NUM)

    records = []
    for _, row in long_df.iterrows():
        records.append({
            "geolocation_name": row["Geolocation"],
            "commodity_name": row["Commodity Description"],
            "year": int(row["year"]),
            "period_name": row["period_name"],
            "period_num": int(row["period_num"]),
            "cpi_value": None if pd.isna(row["cpi_value"]) else float(row["cpi_value"]),
        })
    return records


@dlt.resource(name="cpi_observations", write_disposition="replace")
def cpi_observations():
    csv_text = _fetch_cpi_csv()
    raw_path = _land_raw(csv_text)

    for record in parse_csv_to_records(csv_text):
        record["_raw_snapshot_path"] = str(raw_path)
        yield record


@dlt.source
def psa_cpi_source():
    yield cpi_observations()


# --- Why "replace", not "merge", for now ---
# Same reasoning as World Bank: PSA occasionally revises recent months'
# figures. "replace" means every run reflects current authoritative values
# with no stale duplicate rows. "merge" on (geolocation, commodity, year,
# period) is the natural upgrade once this runs on a schedule long enough
# that a full reload becomes wasteful.