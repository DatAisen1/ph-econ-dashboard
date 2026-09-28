"""
Export assets.

Wraps the export/build_export.py logic as a Dagster asset, depending on the
dbt mart assets (fact_ph_detail, fact_country_comparison, dim_country).

This brings the JSON export into the Dagster lineage graph, so the export
runs automatically after the dbt marts are materialized.
"""

import sys
import pathlib

from dagster import asset, AssetExecutionContext, MaterializeResult, AssetsDefinition

# Make export/ importable so we can reuse build_export.py logic as-is
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "export"))

from build_export import main as build_export_main

WAREHOUSE_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "warehouse.duckdb"
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "web" / "public" / "data"


@asset(
    # Depends on the dbt mart assets. The key format for dbt models in
    # dagster-dbt is [package_name, model_name]. Our dbt project is named
    # "ph_econ" (see transform/dbt_project.yml).
    deps=[
        ["ph_econ", "fact_ph_detail"],
        ["ph_econ", "fact_country_comparison"],
        ["ph_econ", "dim_country"],
    ],
    group_name="export",
    description="Reads dbt marts from warehouse.duckdb and writes static JSON files to web/public/data/.",
)
def json_export(context: AssetExecutionContext) -> MaterializeResult:
    context.log.info(f"Warehouse file: {WAREHOUSE_PATH}")
    context.log.info(f"Output directory: {OUTPUT_DIR}")

    # Reuse the existing build_export.py logic - it's already a self-contained
    # main() function that does exactly what we need.
    build_export_main()

    # Return metadata about what was exported
    import json
    metadata_path = OUTPUT_DIR / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        return MaterializeResult(
            metadata={
                "exported_at_utc": metadata.get("exported_at_utc"),
                "ph_detail_row_count": metadata.get("ph_detail_row_count"),
                "ph_commodity_row_count": metadata.get("ph_commodity_row_count"),
                "country_comparison_indicator_count": metadata.get("country_comparison_indicator_count"),
            }
        )
    else:
        return MaterializeResult(
            metadata={"note": "metadata.json not found, export may have failed"}
        )
