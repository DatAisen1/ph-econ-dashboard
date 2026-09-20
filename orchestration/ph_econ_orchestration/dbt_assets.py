"""
Wraps the existing Phase 3 dbt project (transform/) as Dagster assets.

Why this matters over just calling `dbt run` in a separate script: dagster-dbt
parses the dbt manifest and creates ONE Dagster asset per dbt model
(stg_wb_observations, dim_country, fact_country_comparison), each showing up
as its own node in the lineage graph - not a single opaque "run dbt" blob.
If fact_country_comparison fails, you see THAT node fail, not just "dbt
exited non-zero."

The dbt-to-ingestion link is made WITHOUT a manual `deps` argument
(this dagster-dbt version's @dbt_assets decorator doesn't have one). Instead,
ingestion_assets.py gives wb_observations_ingested the SAME asset key that
dagster-dbt auto-derives for the `raw_wb.wb_observations` dbt source
([source_name, table_name]). Same key = same node, from Dagster's
perspective - dbt's source() reference and our ingestion asset become one
connected graph automatically, and it can't drift out of sync the way a
hand-maintained `deps` list could.
"""

import pathlib
from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

DBT_PROJECT_DIR = pathlib.Path(__file__).parent.parent.parent / "transform"

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,  # our profiles.yml lives inside transform/, not ~/.dbt/
)
# Compiles the manifest.json on `dagster dev` startup in development.
# In production you'd run `dbt parse` as a build step instead of relying
# on this - prepare_if_dev() is explicitly a dev-mode convenience.
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def ph_econ_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()