"""
Ingestion assets.

wb_observations_ingested: wraps the real dlt World Bank pipeline.
psa_cpi_ingested: wraps the real dlt PSA CPI pipeline. Both are now fully
implemented - the "PSA deliberately fails" stub from earlier phases is
gone, since PSA ingestion (and dbt staging/marts on top of it) is real
and tested as of this phase.
"""

import sys
import pathlib

import dlt
from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue

# Make ingestion/ importable so we can reuse worldbank_source.py and
# psa_cpi_source.py as-is, instead of duplicating pipeline logic here.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "ingestion"))

from worldbank_source import worldbank_source  # noqa: E402
from psa_cpi_source import psa_cpi_source  # noqa: E402

COUNTRIES = ["PHL", "IDN", "THA", "VNM", "KOR"]
INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_annual_pct",
    "FP.CPI.TOTL.ZG": "inflation_cpi_annual_pct",
    "SL.UEM.TOTL.ZS": "unemployment_pct_of_labor_force",
    "NY.GDP.PCAP.KD": "gdp_per_capita_constant_usd",
}

# Shared by both assets - same file every caller must agree on, same
# reasoning as ingestion/run_worldbank.py and ingestion/run_psa_cpi.py.
WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "warehouse.duckdb"


@asset(
    # This key MUST match what dagster-dbt derives for the dbt source
    # raw_wb.wb_observations (source_name, table_name) - that's what lets
    # Dagster treat this ingestion asset and the dbt source as the SAME
    # node, automatically wiring dbt's staging model as downstream of this
    # asset with no manual `deps` link to maintain separately.
    key=["raw_wb", "wb_observations"],
    group_name="ingestion",
    description="Runs the World Bank dlt pipeline, landing raw_wb.wb_observations in DuckDB.",
)
def wb_observations_ingested(context: AssetExecutionContext) -> MaterializeResult:
    context.log.info(f"Warehouse file: {WAREHOUSE_PATH}")

    pipeline = dlt.pipeline(
        pipeline_name="worldbank",
        destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
        dataset_name="raw_wb",
    )
    load_info = pipeline.run(
        worldbank_source(countries=COUNTRIES, indicators=INDICATORS)
    )
    context.log.info(str(load_info))

    with pipeline.sql_client() as client:
        row_count = client.execute_sql(
            "SELECT COUNT(*) FROM raw_wb.wb_observations"
        )[0][0]

    return MaterializeResult(
        metadata={"row_count": MetadataValue.int(row_count)}
    )


@asset(
    # Same principle as the WB asset above: this key must match what
    # dagster-dbt derives for the raw_psa.cpi_observations dbt source, so
    # stg_psa_cpi wires up as downstream automatically.
    key=["raw_psa", "cpi_observations"],
    group_name="ingestion",
    description="Runs the PSA OpenSTAT CPI dlt pipeline, landing raw_psa.cpi_observations in DuckDB.",
)
def psa_cpi_ingested(context: AssetExecutionContext) -> MaterializeResult:
    context.log.info(f"Warehouse file: {WAREHOUSE_PATH}")

    pipeline = dlt.pipeline(
        pipeline_name="psa",
        destination=dlt.destinations.duckdb(str(WAREHOUSE_PATH)),
        dataset_name="raw_psa",
    )
    load_info = pipeline.run(psa_cpi_source())
    context.log.info(str(load_info))

    with pipeline.sql_client() as client:
        row_count = client.execute_sql(
            "SELECT COUNT(*) FROM raw_psa.cpi_observations"
        )[0][0]

    return MaterializeResult(
        metadata={"row_count": MetadataValue.int(row_count)}
    )