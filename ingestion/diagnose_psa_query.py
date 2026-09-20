"""
Diagnostic: run several PSA CPI queries of increasing size and compare
expected cell count (product of dimension sizes) against actual len(value).
Helps isolate whether the "1 value returned" problem is about total cell
count, a specific dimension, or something else.

Run this directly - it's a standalone script, not part of the pipeline.
Respects the 10-req/10s rate limit via psa_http_client's limiter.
"""

import sys
import pathlib
import json

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from psa_http_client import build_session, psa_rate_limiter, PXWEB_BASE

TABLE_PATH = "DB/2M/PI/CPI/2018NEW/0012M4ACP22.px"
session = build_session()


def run_query(label, geo_codes, commodity_codes, year_codes, period_codes):
    query = {
        "query": [
            {"code": "Geolocation", "selection": {"filter": "item", "values": geo_codes}},
            {"code": "Commodity Description", "selection": {"filter": "item", "values": commodity_codes}},
            {"code": "Year", "selection": {"filter": "item", "values": year_codes}},
            {"code": "Period", "selection": {"filter": "item", "values": period_codes}},
        ],
        "response": {"format": "json-stat2"},
    }
    expected = len(geo_codes) * len(commodity_codes) * len(year_codes) * len(period_codes)

    psa_rate_limiter.wait_if_needed()
    resp = session.post(f"{PXWEB_BASE}/{TABLE_PATH}", json=query, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    actual = len(payload.get("value", []))
    size = payload.get("size")
    status = "OK" if actual == expected else "MISMATCH"
    print(f"[{status}] {label}: expected={expected} actual_len(value)={actual} size={size}")
    return payload


print("--- Test 1: absolute minimum (1 cell) ---")
run_query("1 geo x 1 commodity x 1 year x 1 period", ["0"], ["0"], ["0"], ["0"])

print("\n--- Test 2: 1 geo, 1 commodity, 1 year, ALL 12 periods ---")
run_query("1 geo x 1 commodity x 1 year x 12 periods", ["0"], ["0"], ["0"], [str(i) for i in range(12)])

print("\n--- Test 3: 1 geo, 1 commodity, ALL 9 years, 1 period ---")
run_query("1 geo x 1 commodity x 9 years x 1 period", ["0"], ["0"], [str(i) for i in range(9)], ["0"])

print("\n--- Test 4: ALL 3 geos, 1 commodity, 1 year, 1 period ---")
run_query("3 geo x 1 commodity x 1 year x 1 period", ["0", "1", "2"], ["0"], ["0"], ["0"])

print("\n--- Test 5: the original full query (3 x 1 x 9 x 12 = 324) ---")
full = run_query("3 geo x 1 commodity x 9 years x 12 periods", ["0", "1", "2"], ["0"],
                  [str(i) for i in range(9)], [str(i) for i in range(12)])

# Save the full response so we can inspect it further if needed without another request
out_path = pathlib.Path(__file__).parent.parent / "raw" / "psa" / "diagnostic_full.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(full, indent=2))
print(f"\nFull response saved to: {out_path}")