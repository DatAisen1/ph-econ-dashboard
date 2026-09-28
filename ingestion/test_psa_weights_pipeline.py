"""
Tests for the PSA Weights pipeline.

The fixture below represents the expected CSV shape for the weights table:
one row per geolocation, one column per commodity (no time dimension).
"""

import pathlib
import shutil
from unittest.mock import patch
import dlt
from psa_weights_source import parse_csv_to_records, psa_weights_source, RAW_LANDING_DIR

TEST_DB_PATH = pathlib.Path("psa_weights_test.duckdb")

# Fixture representing the actual CSV shape: 3 columns (Geolocation, Commodity Description, Weights)
# One row per (geolocation, commodity) combination, already in long format
WEIGHTS_FIXTURE = (
    '"Geolocation","Commodity Description","Weights"\r\n'
    '"PHILIPPINES","0 - ALL ITEMS",100.0\r\n'
    '"PHILIPPINES","01 - Food and non-alcoholic beverages",45.2\r\n'
    '"PHILIPPINES","02 - Alcoholic beverages and tobacco",2.1\r\n'
    '"PHILIPPINES","03 - Clothing and footwear",3.5\r\n'
    '"..National Capital Region (NCR)","0 - ALL ITEMS",100.0\r\n'
    '"..National Capital Region (NCR)","01 - Food and non-alcoholic beverages",42.8\r\n'
    '"..National Capital Region (NCR)","02 - Alcoholic beverages and tobacco",2.5\r\n'
    '"..National Capital Region (NCR)","03 - Clothing and footwear",4.0\r\n'
    '"..Areas Outside National Capital Region (AONCR)","0 - ALL ITEMS",100.0\r\n'
    '"..Areas Outside National Capital Region (AONCR)","01 - Food and non-alcoholic beverages",46.5\r\n'
    '"..Areas Outside National Capital Region (AONCR)","02 - Alcoholic beverages and tobacco",1.9\r\n'
    '"..Areas Outside National Capital Region (AONCR)","03 - Clothing and footwear",3.2\r\n'
)


def test_parse_produces_correct_row_count():
    """3 geolocations x 4 commodities = 12 rows (already in long format)."""
    records = parse_csv_to_records(WEIGHTS_FIXTURE)
    assert len(records) == 12


def test_parse_melts_wide_columns_correctly():
    records = parse_csv_to_records(WEIGHTS_FIXTURE)
    phl_all_items = [
        r for r in records
        if r["geolocation_name"] == "PHILIPPINES" and r["commodity_name"] == "0 - ALL ITEMS"
    ]
    assert len(phl_all_items) == 1
    assert phl_all_items[0]["weight_value"] == 100.0


def test_parse_handles_all_three_geolocations():
    records = parse_csv_to_records(WEIGHTS_FIXTURE)
    geos = {r["geolocation_name"] for r in records}
    assert geos == {"PHILIPPINES", "..National Capital Region (NCR)", "..Areas Outside National Capital Region (AONCR)"}


def test_pipeline_loads_and_lands_raw_csv():
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)

    with patch("psa_weights_source._fetch_weights_csv", return_value=WEIGHTS_FIXTURE):
        pipeline = dlt.pipeline(
            pipeline_name="psa_weights_test",
            destination=dlt.destinations.duckdb(str(TEST_DB_PATH)),
            dataset_name="raw_psa_test",
        )
        load_info = pipeline.run(psa_weights_source())
        assert not load_info.has_failed_jobs, load_info

        with pipeline.sql_client() as client:
            count = client.execute_sql("SELECT COUNT(*) FROM raw_psa_test.cpi_weights")[0][0]

    assert count == 12

    raw_files = list(RAW_LANDING_DIR.glob("weights_*.csv"))
    assert len(raw_files) == 1, "expected exactly one raw CSV snapshot to be written"

    print(f"PASSED: 12 rows loaded via dlt, raw snapshot at {raw_files[0]}")


def test_merge_write_disposition_updates_existing_rows():
    """
    Verify that merge write_disposition updates existing rows without creating
    duplicates. Run the pipeline twice with a changed value and confirm:
    1. Row count does NOT double (stays at 12)
    2. The changed value is reflected in the updated row
    """
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)

    # First run with original values
    with patch("psa_weights_source._fetch_weights_csv", return_value=WEIGHTS_FIXTURE):
        pipeline = dlt.pipeline(
            pipeline_name="psa_weights_test_merge",
            destination=dlt.destinations.duckdb(str(TEST_DB_PATH)),
            dataset_name="raw_psa_test_merge",
        )
        load_info = pipeline.run(psa_weights_source())
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count_1 = client.execute_sql("SELECT COUNT(*) FROM raw_psa_test_merge.cpi_weights")[0][0]
        assert count_1 == 12, f"Expected 12 rows after first run, got {count_1}"

    # Second run with a changed value (PHL ALL ITEMS weight revised from 100.0 to 105.0)
    fixture_payload_2 = (
        '"Geolocation","Commodity Description","Weights"\r\n'
        '"PHILIPPINES","0 - ALL ITEMS",105.0\r\n'
        '"PHILIPPINES","01 - Food and non-alcoholic beverages",45.2\r\n'
        '"PHILIPPINES","02 - Alcoholic beverages and tobacco",2.1\r\n'
        '"PHILIPPINES","03 - Clothing and footwear",3.5\r\n'
        '"..National Capital Region (NCR)","0 - ALL ITEMS",100.0\r\n'
        '"..National Capital Region (NCR)","01 - Food and non-alcoholic beverages",42.8\r\n'
        '"..National Capital Region (NCR)","02 - Alcoholic beverages and tobacco",2.5\r\n'
        '"..National Capital Region (NCR)","03 - Clothing and footwear",4.0\r\n'
        '"..Areas Outside National Capital Region (AONCR)","0 - ALL ITEMS",100.0\r\n'
        '"..Areas Outside National Capital Region (AONCR)","01 - Food and non-alcoholic beverages",46.5\r\n'
        '"..Areas Outside National Capital Region (AONCR)","02 - Alcoholic beverages and tobacco",1.9\r\n'
        '"..Areas Outside National Capital Region (AONCR)","03 - Clothing and footwear",3.2\r\n'
    )

    with patch("psa_weights_source._fetch_weights_csv", return_value=fixture_payload_2):
        load_info = pipeline.run(psa_weights_source())
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count_2 = client.execute_sql("SELECT COUNT(*) FROM raw_psa_test_merge.cpi_weights")[0][0]
        assert count_2 == 12, f"Expected 12 rows after second run (merge, not append), got {count_2}"

        # Verify the PHL ALL ITEMS value was updated
        phl_all_items_value = client.execute_sql(
            "SELECT weight_value FROM raw_psa_test_merge.cpi_weights "
            "WHERE geolocation_name = 'PHILIPPINES' AND commodity_name = '0 - ALL ITEMS'"
        )[0][0]
        assert phl_all_items_value == 105.0, f"Expected PHL ALL ITEMS value to be updated to 105.0, got {phl_all_items_value}"

    print("PASSED (merge write_disposition): row count stable at 12, PHL ALL ITEMS value updated correctly")


if __name__ == "__main__":
    test_parse_produces_correct_row_count()
    test_parse_melts_wide_columns_correctly()
    test_parse_handles_all_three_geolocations()
    test_pipeline_loads_and_lands_raw_csv()
    test_merge_write_disposition_updates_existing_rows()
    TEST_DB_PATH.unlink(missing_ok=True)
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)
    print("ALL PASSED: 5/5")
