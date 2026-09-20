"""
Run this ONCE to discover the real dimension codes for the PSA CPI table.

PXWeb tables expose their metadata via a plain GET request to the table's
API URL (no JSON body needed) - it returns the list of "variables" (Geolocation,
Commodity Description, Year, Period) and every valid "value" code for each.
We can't guess these codes; they're specific to this one table, and PXWeb
sometimes uses index-encoded values ("37" meaning some specific year) rather
than literal labels, as PSA's own docs example shows for a different table.

Usage:
    python ingestion/discover_psa_metadata.py

This makes exactly ONE request, so it doesn't need the rate limiter -
that's reserved for the real ingestion pipeline once we know what to ask for.
"""

import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from psa_http_client import build_session, PXWEB_BASE

# Table: "Consumer Price Index for All Income Households by Commodity Group
# (2018=100): January 2018 - August 2026"
# Path confirmed from openstat.psa.gov.ph's own site navigation on 2026-09-18.
TABLE_PATH = "DB/2M/PI/CPI/2018NEW/0012M4ACP22.px"


def main():
    session = build_session()
    url = f"{PXWEB_BASE}/{TABLE_PATH}"

    print(f"GET {url}")
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    metadata = resp.json()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    print("\n--- SUMMARY (paste this whole block back to me) ---")
    for variable in metadata.get("variables", []):
        code = variable.get("code")
        text = variable.get("text")
        values = variable.get("values", [])
        value_texts = variable.get("valueTexts", [])
        print(f"\nVariable code='{code}' (\"{text}\") - {len(values)} values")
        # Print first 10 so it's readable even for the 354-value commodity list
        for v, vt in list(zip(values, value_texts))[:10]:
            print(f"    {v!r} = {vt!r}")
        if len(values) > 10:
            print(f"    ... and {len(values) - 10} more")


if __name__ == "__main__":
    main()