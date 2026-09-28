"""
dlt source for PSA OpenSTAT's CPI Weights table.

Table: "Consumer Price Index for All Income Households by Commodity Group
(2018=100): Weights", 0012M4ACP12.px.

SCOPE:
  - Geolocation: PHILIPPINES + all 18 top-level regions (SAME 19 codes as
    psa_cpi_source.py's GEOLOCATION_CODES).
  - Commodity Description: ALL ITEMS + all 13 top-level commodity divisions
    (SAME 14 codes as psa_cpi_source.py's COMMODITY_CODES).
  - NO Year/Period dimension exists on this table - weights are static,
    not time-series data.

RESPONSE SHAPE: Since there's no time dimension, the CSV layout is:
- 3 columns: Geolocation, Commodity Description, Weights
- One row per (geolocation, commodity) combination
- Already in long format (no melting needed, unlike the CPI table which
  has columns for each Year+Period combination)
"""

import io
import pathlib
import datetime

import dlt
import pandas as pd

from psa_http_client import build_session, psa_rate_limiter, PXWEB_BASE

TABLE_PATH = "DB/2M/PI/CPI/2018/0012M4ACP12.px"

# Same codes as psa_cpi_source.py - confirmed via discover_psa_expansion.py
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

RAW_LANDING_DIR = pathlib.Path(__file__).resolve().parent.parent / "raw" / "psa"

_session = build_session()


def _build_query() -> dict:
    return {
        "query": [
            {"code": "Geolocation", "selection": {"filter": "item", "values": GEOLOCATION_CODES}},
            {"code": "Commodity Description", "selection": {"filter": "item", "values": COMMODITY_CODES}},
        ],
        "response": {"format": "csv"},
    }


def _land_raw(csv_text: str) -> pathlib.Path:
    RAW_LANDING_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = RAW_LANDING_DIR / f"weights_{ts}.csv"
    path.write_text(csv_text)
    return path


def _fetch_weights_csv() -> str:
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
    Pure function (no I/O) so it's independently testable against a fixture.

    The weights table CSV layout is:
    - 3 columns: Geolocation, Commodity Description, Weights
    - One row per (geolocation, commodity) combination
    - No melting needed - already in long format
    """
    df = pd.read_csv(io.StringIO(csv_text), na_values=["..", "-", ""])

    records = []
    for _, row in df.iterrows():
        records.append({
            "geolocation_name": row["Geolocation"],
            "commodity_name": row["Commodity Description"],
            "weight_value": None if pd.isna(row["Weights"]) else float(row["Weights"]),
        })
    return records


@dlt.resource(
    name="cpi_weights",
    write_disposition="merge",
    primary_key=("geolocation_name", "commodity_name"),
)
def cpi_weights():
    csv_text = _fetch_weights_csv()
    raw_path = _land_raw(csv_text)

    for record in parse_csv_to_records(csv_text):
        record["_raw_snapshot_path"] = str(raw_path)
        yield record


@dlt.source
def psa_weights_source():
    yield cpi_weights()


# --- Why "merge", not "replace" or "append", for this table ---
# Same reasoning as PSA CPI: weights are static reference data that PSA
# occasionally revises. "append" would add duplicate rows for the same
# (geolocation, commodity) on every run. "replace" wipes the entire table
# on each run, which is safe but wasteful for a mature pipeline.
#
# "merge" (upsert on a primary key) is the correct choice: it updates
# existing (geolocation, commodity) rows with revised values and inserts
# new ones, without wiping history. With the composite primary key
# (geolocation_name, commodity_name), each weight has exactly one row
# that reflects the most recent authoritative value from PSA.
