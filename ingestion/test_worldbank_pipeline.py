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


if __name__ == "__main__":
    test_fast_path_single_combined_call()
    test_fallback_path_when_combined_call_fails()
    TEST_DB_PATH.unlink(missing_ok=True)