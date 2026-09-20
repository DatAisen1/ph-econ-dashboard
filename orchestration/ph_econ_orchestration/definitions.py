from dagster import Definitions, define_asset_job, ScheduleDefinition
from dagster_dbt import DbtCliResource

from .ingestion_assets import wb_observations_ingested, psa_cpi_ingested
from .dbt_assets import ph_econ_dbt_assets, dbt_project

all_assets_job = define_asset_job(name="ph_econ_daily_refresh", selection="*")

# Daily is a deliberate choice, not a default: PSA publishes monthly/quarterly,
# World Bank annually. There is no data-freshness reason to run this hourly -
# doing so would just hammer both free APIs for no new information. Match
# schedule cadence to actual source update frequency, not to "shorter feels
# more real-time."
daily_schedule = ScheduleDefinition(
    job=all_assets_job,
    cron_schedule="0 6 * * *",  # 06:00 daily
)

defs = Definitions(
    assets=[wb_observations_ingested, psa_cpi_ingested, ph_econ_dbt_assets],
    jobs=[all_assets_job],
    schedules=[daily_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=dbt_project),
    },
)