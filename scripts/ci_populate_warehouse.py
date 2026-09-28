"""
CI-only fixture script: populates warehouse.duckdb with minimal mocked data
so dbt can run without hitting live APIs in CI.

This script reuses the exact mock patterns from the existing test files:
- ingestion/test_worldbank_pipeline.py patches worldbank_source._session.get
- ingestion/test_psa_cpi_pipeline.py patches psa_cpi_source._fetch_cpi_csv

Run this before dbt seed/run/test in CI.
"""

import pathlib
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add ingestion/ to path so we can import the sources
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "ingestion"))

import dlt
from worldbank_source import worldbank_source
from psa_cpi_source import psa_cpi_source, RAW_LANDING_DIR

WAREHOUSE_PATH = pathlib.Path(__file__).parent.parent / "warehouse.duckdb"

# Minimal fixture data matching the test patterns
WB_FIXTURE_PAYLOAD = (
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

PSA_CPI_FIXTURE = (
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
)


def _mock_worldbank_ingestion():
    """Populate raw_wb.wb_observations with minimal fixture data."""
    print("Populating raw_wb.wb_observations with CI fixture data...")

    mock_response = MagicMock()
    mock_response.json.return_value = WB_FIXTURE_PAYLOAD
    mock_response.raise_for_status.return_value = None
    mock_get = MagicMock(return_value=mock_response)

    with patch("worldbank_source._session.get", mock_get):
        pipeline = dlt.pipeline(
            pipeline_name="worldbank_ci",
            destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
            dataset_name="raw_wb",
        )
        load_info = pipeline.run(
            worldbank_source(
                countries=["PHL", "IDN"],
                indicators={"NY.GDP.MKTP.CD": "gdp_current_usd"}
            )
        )
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count = client.execute_sql("SELECT COUNT(*) FROM raw_wb.wb_observations")[0][0]
    print(f"Loaded {count} rows into raw_wb.wb_observations")


def _mock_psa_cpi_ingestion():
    """Populate raw_psa.cpi_observations with minimal fixture data."""
    print("Populating raw_psa.cpi_observations with CI fixture data...")

    # Clean up any existing raw landing directory
    shutil.rmtree(RAW_LANDING_DIR, ignore_errors=True)

    with patch("psa_cpi_source._fetch_cpi_csv", return_value=PSA_CPI_FIXTURE):
        pipeline = dlt.pipeline(
            pipeline_name="psa_ci",
            destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
            dataset_name="raw_psa",
        )
        load_info = pipeline.run(psa_cpi_source())
        assert not load_info.has_failed_jobs, load_info

    with pipeline.sql_client() as client:
        count = client.execute_sql("SELECT COUNT(*) FROM raw_psa.cpi_observations")[0][0]
    print(f"Loaded {count} rows into raw_psa.cpi_observations")


def main():
    # Ensure warehouse doesn't exist from previous runs
    WAREHOUSE_PATH.unlink(missing_ok=True)

    print(f"Creating CI fixture warehouse at {WAREHOUSE_PATH}")
    _mock_worldbank_ingestion()
    _mock_psa_cpi_ingestion()
    print("CI fixture warehouse populated successfully")


if __name__ == "__main__":
    main()
