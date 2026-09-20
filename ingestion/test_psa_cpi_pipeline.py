"""
Tests for the PSA CPI pipeline. REAL_CSV_FIXTURE below is not synthetic -
it's the actual response body PSA's live API returned for a 3-geolocation
x 2-year query (confirmed by the user running diagnose_psa_csv.py against
the real API on 2026-09-19). Testing against real server output, rather
than a hand-built guess, gives much higher confidence the parser handles
what PSA actually sends - trailing-zero decimal formatting, the ".." for
missing values, the exact quoting style, all included as-is.
"""

import pathlib
import shutil
from unittest.mock import patch
import dlt
from psa_cpi_source import parse_csv_to_records, psa_cpi_source, RAW_LANDING_DIR

TEST_DB_PATH = pathlib.Path("psa_test.duckdb")

REAL_CSV_FIXTURE = (
    '"Geolocation","Commodity Description","2018 Jan","2018 Feb","2018 Mar","2018 Apr",'
    '"2018 May","2018 Jun","2018 Jul","2018 Aug","2018 Sep","2018 Oct","2018 Nov","2018 Dec",'
    '"2019 Jan","2019 Feb","2019 Mar","2019 Apr","2019 May","2019 Jun","2019 Jul","2019 Aug",'
    '"2019 Sep","2019 Oct","2019 Nov","2019 Dec"\r\n'
    '"PHILIPPINES","0 - ALL ITEMS",97.2000000000000,97.9000000000000,98.4000000000000,'
    '98.8000000000000,99.0000000000000,99.4000000000000,100.2000000000000,101.1000000000000,'
    '102.1000000000000,102.3000000000000,102.0000000000000,101.4000000000000,101.5000000000000,'
    '101.6000000000000,101.7000000000000,102.0000000000000,102.2000000000000,102.1000000000000,'
    '102.4000000000000,102.5000000000000,102.6000000000000,102.9000000000000,103.2000000000000,'
    '103.8000000000000\r\n'
    '"..National Capital Region (NCR)","0 - ALL ITEMS",96.9000000000000,98.0000000000000,'
    '99.0000000000000,99.3000000000000,99.2000000000000,99.6000000000000,100.4000000000000,'
    '101.2000000000000,101.8000000000000,101.7000000000000,101.7000000000000,101.2000000000000,'
    '101.4000000000000,101.7000000000000,101.8000000000000,102.2000000000000,102.4000000000000,'
    '102.3000000000000,102.4000000000000,102.4000000000000,102.3000000000000,102.7000000000000,'
    '103.1000000000000,103.9000000000000\r\n'
    '"..Areas Outside National Capital Region (AONCR)","0 - ALL ITEMS",97.3000000000000,'
    '97.9000000000000,98.3000000000000,98.7000000000000,98.9000000000000,99.4000000000000,'
    '100.2000000000000,101.1000000000000,102.2000000000000,102.4000000000000,102.1000000000000,'
    '101.4000000000000,101.5000000000000,101.6000000000000,101.7000000000000,101.9000000000000,'
    '102.1000000000000,102.1000000000000,102.4000000000000,102.5000000000000,102.7000000000000,'
    '102.9000000000000,103.2000000000000,103.8000000000000'
)


def test_parse_produces_correct_row_count():
    """3 geolocations x 24 (year, period) columns = 72 long-format rows."""
    records = parse_csv_to_records(REAL_CSV_FIXTURE)
    assert len(records) == 72


def test_parse_melts_wide_columns_correctly():
    records = parse_csv_to_records(REAL_CSV_FIXTURE)
    phl_jan_2018 = [
        r for r in records
        if r["geolocation_name"] == "PHILIPPINES" and r["year"] == 2018 and r["period_name"] == "Jan"
    ]
    assert len(phl_jan_2018) == 1
    assert phl_jan_2018[0]["cpi_value"] == 97.2
    assert phl_jan_2018[0]["period_num"] == 1


def test_parse_handles_all_three_geolocations():
    records = parse_csv_to_records(REAL_CSV_FIXTURE)
    geos = {r["geolocation_name"] for r in records}
    assert geos == {"PHILIPPINES", "..National Capital Region (NCR)", "..Areas Outside National Capital Region (AONCR)"}


def test_pipeline_loads_and_lands_raw_csv():
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)

    with patch("psa_cpi_source._fetch_cpi_csv", return_value=REAL_CSV_FIXTURE):
        pipeline = dlt.pipeline(
            pipeline_name="psa_test",
            destination=dlt.destinations.duckdb(str(TEST_DB_PATH)),
            dataset_name="raw_psa_test",
        )
        load_info = pipeline.run(psa_cpi_source())
        assert not load_info.has_failed_jobs, load_info

        with pipeline.sql_client() as client:
            count = client.execute_sql("SELECT COUNT(*) FROM raw_psa_test.cpi_observations")[0][0]

    assert count == 72

    raw_files = list(RAW_LANDING_DIR.glob("cpi_*.csv"))
    assert len(raw_files) == 1, "expected exactly one raw CSV snapshot to be written"

    print(f"PASSED: 72 rows loaded via dlt, raw snapshot at {raw_files[0]}")


if __name__ == "__main__":
    test_parse_produces_correct_row_count()
    test_parse_melts_wide_columns_correctly()
    test_parse_handles_all_three_geolocations()
    test_pipeline_loads_and_lands_raw_csv()
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)
    print("ALL PASSED: 4/4")