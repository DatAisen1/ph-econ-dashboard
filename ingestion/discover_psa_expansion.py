"""
Run this ONCE to discover:
1. The FULL list of Geolocation codes (all ~18 top-level regions, not
   just the first 10 we saw truncated before).
2. The top-level Commodity Description codes (the 13 major divisions -
   "01 FOOD AND NON-ALCOHOLIC BEVERAGES", "07 TRANSPORT", etc. - not the
   full 354-way granular breakdown).
3. The metadata for the SEPARATE weights table (0012M4ACP12.px), which
   has a different structure from the CPI index table we already use.

Usage:
    python ingestion/discover_psa_expansion.py
"""

import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from psa_http_client import build_session, PXWEB_BASE

CPI_TABLE_PATH = "DB/2M/PI/CPI/2018NEW/0012M4ACP22.px"
WEIGHTS_TABLE_PATH = "DB/2M/PI/CPI/2018/0012M4ACP12.px"


def fetch_metadata(session, table_path):
    url = f"{PXWEB_BASE}/{table_path}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    session = build_session()

    print("=" * 60)
    print("1. FULL GEOLOCATION LIST (from the CPI index table)")
    print("=" * 60)
    cpi_metadata = fetch_metadata(session, CPI_TABLE_PATH)
    for variable in cpi_metadata["variables"]:
        if variable["code"] == "Geolocation":
            values = variable["values"]
            texts = variable["valueTexts"]
            print(f"Total geolocation values: {len(values)}\n")
            print("--- ALL entries (region-level = exactly TWO leading dots) ---")
            for v, t in zip(values, texts):
                dot_count = len(t) - len(t.lstrip("."))
                marker = " <-- REGION LEVEL" if dot_count == 2 or dot_count == 0 else ""
                print(f"  {v!r} = {t!r}{marker}")

        if variable["code"] == "Commodity Description":
            values = variable["values"]
            texts = variable["valueTexts"]
            print("\n" + "=" * 60)
            print("2. TOP-LEVEL COMMODITY DIVISIONS (2-digit codes only, e.g. '01 FOOD...')")
            print("=" * 60)
            for v, t in zip(values, texts):
                # Top-level divisions look like "01 - FOOD AND NON-ALCOHOLIC BEVERAGES"
                # (a 2-digit code, no further dots/sub-levels) vs.
                # "01.1 - FOOD" (has a sub-level). Filter for the coarse ones.
                label_part = t.split(" - ", 1)[0].strip()
                if label_part.isdigit() or (len(label_part) == 2 and label_part.isdigit()):
                    print(f"  {v!r} = {t!r}")
                elif label_part == "0":
                    print(f"  {v!r} = {t!r}  <-- ALL ITEMS (already have this)")

    print("\n" + "=" * 60)
    print("3. WEIGHTS TABLE METADATA")
    print("=" * 60)
    weights_metadata = fetch_metadata(session, WEIGHTS_TABLE_PATH)

    # Save the FULL, untruncated response to disk - we'll want to refer
    # back to this while building the actual ingestion parser.
    out_path = pathlib.Path(__file__).parent.parent / "raw" / "psa" / "weights_metadata_full.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(weights_metadata, indent=2, ensure_ascii=False))
    print(f"Full metadata saved to: {out_path}\n")

    # Print each variable's structure explicitly (not a raw truncated
    # dump) - same summary format as discover_psa_metadata.py, readable
    # regardless of how many values a variable has.
    for variable in weights_metadata["variables"]:
        code = variable.get("code")
        text = variable.get("text")
        values = variable.get("values", [])
        value_texts = variable.get("valueTexts", [])
        print(f"Variable code={code!r} (\"{text}\") - {len(values)} values")
        for v, vt in list(zip(values, value_texts))[:8]:
            print(f"    {v!r} = {vt!r}")
        if len(values) > 8:
            print(f"    ... and {len(values) - 8} more (see saved file for all)")
        print()



if __name__ == "__main__":
    main()