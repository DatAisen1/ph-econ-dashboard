"""
Validates the refactored dlt source against fixtures - no network required.

Two scenarios matter here, because the source now has two code paths:
1. The combined multi-country + multi-indicator call succeeds (fast path).
2. The combined call fails and the code falls back to per-indicator calls
   (still country-batched). This is the path that protects us if the
   indicator-batching syntax turns out not to work the way the docs imply.
"""

import pathlib
from unittest.mock import patch, MagicMock
import dlt
from worldbank_source import worldbank_source

TEST_DB_PATH = pathlib.Path("worldbank_test.duckdb")

INDICATORS = {"NY.GDP.MKTP.CD": "gdp_current_usd"}
COUNTRIES = ["PHL", "IDN"]


def _fixture_payload():
    return (
        {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "PH", "value": "Philippines"},
                "countryiso3code": "PHL",
                "date": "2023",
                "value": 437147404860.9,
                "unit": "",
            },
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "ID", "value": "Indonesia"},
                "countryiso3code": "IDN",
                "date": "2023",
                "value": 1371171607679.0,
                "unit": "",
            },
        ],
    )


def _run_pipeline(mock_get, dataset_name: str):
    TEST_DB_PATH.unlink(missing_ok=True)
    with patch("worldbank_source._session.get", mock_get):
        pipeline = dlt.pipeline(
            pipeline_name=f"worldbank_test_{dataset_name}",
            destination=dlt.destinations.duckdb(str(TEST_DB_PATH)),
            dataset_name=dataset_name,
        )
        load_info = pipeline.run(
            worldbank_source(countries=COUNTRIES, indicators=INDICATORS)
        )
        assert not load_info.has_failed_jobs, load_info
        with pipeline.sql_client() as client:
            rows = list(
                client.execute_sql(
                    f"SELECT country_code, indicator_code, year, value "
                    f"FROM {dataset_name}.wb_observations ORDER BY country_code"
                )
            )
        return rows


def test_fast_path_single_combined_call():
    """The combined multi-country + multi-indicator call succeeds directly."""
    mock_response = MagicMock()
    mock_response.json.return_value = _fixture_payload()
    mock_response.raise_for_status.return_value = None
    mock_get = MagicMock(return_value=mock_response)

    rows = _run_pipeline(mock_get, "raw_wb_test_fast")

    assert len(rows) == 2
    assert rows[0][:3] == ("IDN", "NY.GDP.MKTP.CD", 2023)
    # Exactly ONE HTTP call for one country batch x one combined indicator
    # set - this is the number we're actually optimizing for.
    assert mock_get.call_count == 1
    print(f"PASSED (fast path): {mock_get.call_count} HTTP call for 2 countries x 1 indicator")


def test_fallback_path_when_combined_call_fails():
    """
    The combined call raises (simulating source=2 rejecting the request);
    the resource must recover via the per-indicator fallback and still
    produce correct rows.
    """
    error_response = MagicMock()
    error_response.json.return_value = {"error": "invalid"}  # triggers our ValueError branch
    error_response.raise_for_status.return_value = None

    ok_response = MagicMock()
    ok_response.json.return_value = _fixture_payload()
    ok_response.raise_for_status.return_value = None

    # First call (combined) fails-shaped, second call (fallback, per-indicator) succeeds.
    mock_get = MagicMock(side_effect=[error_response, ok_response])

    rows = _run_pipeline(mock_get, "raw_wb_test_fallback")

    assert len(rows) == 2
    assert mock_get.call_count == 2  # 1 failed combined attempt + 1 fallback call
    print(f"PASSED (fallback path): recovered after {mock_get.call_count} calls")


def test_merge_write_disposition_updates_existing_rows():
    """
    Verify that merge write_disposition updates existing rows without creating
    duplicates. Run the pipeline twice with a changed value and confirm:
    1. Row count does NOT double (stays at 2)
    2. The changed value is reflected in the updated row
    """
    TEST_DB_PATH.unlink(missing_ok=True)

    # First run with original values
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = _fixture_payload()
    mock_response_1.raise_for_status.return_value = None
    mock_get_1 = MagicMock(return_value=mock_response_1)

    with patch("worldbank_source._session.get", mock_get_1):
        pipeline = dlt.pipeline(
            pipeline_name="worldbank_test_merge",
            destination=dlt.destinations.duckdb(str(TEST_DB_PATH)),
            dataset_name="raw_wb_test_merge",
        )
        load_info = pipeline.run(
            worldbank_source(countries=COUNTRIES, indicators=INDICATORS)
        )
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count_1 = client.execute_sql("SELECT COUNT(*) FROM raw_wb_test_merge.wb_observations")[0][0]
        assert count_1 == 2, f"Expected 2 rows after first run, got {count_1}"

    # Second run with a changed value (PHL GDP revised from 437147404860.9 to 450000000000.0)
    fixture_payload_2 = (
        {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "PH", "value": "Philippines"},
                "countryiso3code": "PHL",
                "date": "2023",
                "value": 450000000000.0,  # REVISED VALUE
                "unit": "",
            },
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "ID", "value": "Indonesia"},
                "countryiso3code": "IDN",
                "date": "2023",
                "value": 1371171607679.0,  # unchanged
                "unit": "",
            },
        ],
    )

    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = fixture_payload_2
    mock_response_2.raise_for_status.return_value = None
    mock_get_2 = MagicMock(return_value=mock_response_2)

    with patch("worldbank_source._session.get", mock_get_2):
        load_info = pipeline.run(
            worldbank_source(countries=COUNTRIES, indicators=INDICATORS)
        )
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count_2 = client.execute_sql("SELECT COUNT(*) FROM raw_wb_test_merge.wb_observations")[0][0]
        assert count_2 == 2, f"Expected 2 rows after second run (merge, not append), got {count_2}"

        # Verify the PHL value was updated
        phl_value = client.execute_sql(
            "SELECT value FROM raw_wb_test_merge.wb_observations "
            "WHERE country_code = 'PHL' AND indicator_code = 'NY.GDP.MKTP.CD' AND year = 2023"
        )[0][0]
        assert phl_value == 450000000000.0, f"Expected PHL value to be updated to 450000000000.0, got {phl_value}"

        # Verify IDN value stayed the same
        idn_value = client.execute_sql(
            "SELECT value FROM raw_wb_test_merge.wb_observations "
            "WHERE country_code = 'IDN' AND indicator_code = 'NY.GDP.MKTP.CD' AND year = 2023"
        )[0][0]
        assert idn_value == 1371171607679.0, f"Expected IDN value to stay 1371171607679.0, got {idn_value}"

    print("PASSED (merge write_disposition): row count stable at 2, PHL value updated correctly")


if __name__ == "__main__":
    test_fast_path_single_combined_call()
    test_fallback_path_when_combined_call_fails()
    test_merge_write_disposition_updates_existing_rows()
    TEST_DB_PATH.unlink(missing_ok=True)
    print("ALL PASSED: 3/3")