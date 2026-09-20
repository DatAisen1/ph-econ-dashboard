"""
One-off check: does format=csv actually return the expected number of rows,
where format=json-stat2 mysteriously always returned exactly 1 value?

Run this directly.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from psa_http_client import build_session, psa_rate_limiter, PXWEB_BASE

TABLE_PATH = "DB/2M/PI/CPI/2018NEW/0012M4ACP22.px"
session = build_session()

query = {
    "query": [
        {"code": "Geolocation", "selection": {"filter": "item", "values": ["0", "1", "2"]}},
        {"code": "Commodity Description", "selection": {"filter": "item", "values": ["0"]}},
        {"code": "Year", "selection": {"filter": "item", "values": ["0", "1"]}},  # just 2018,2019 for this check
        {"code": "Period", "selection": {"filter": "item", "values": [str(i) for i in range(12)]}},
    ],
    "response": {"format": "csv"},
}
expected_rows = 3 * 1 * 2 * 12  # = 72

psa_rate_limiter.wait_if_needed()
resp = session.post(f"{PXWEB_BASE}/{TABLE_PATH}", json=query, timeout=60)
resp.raise_for_status()

csv_text = resp.text
lines = csv_text.strip().split("\n")

print(f"Expected data rows: {expected_rows}")
print(f"Actual lines returned (including header): {len(lines)}")
print(f"Actual data rows (excluding header): {len(lines) - 1}")
print("\n--- First 5 lines (raw CSV) ---")
for line in lines[:5]:
    print(repr(line))

out_path = pathlib.Path(__file__).parent.parent / "raw" / "psa" / "diagnostic.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(csv_text)
print(f"\nFull CSV saved to: {out_path}")