-- Staging: rename/cast ONLY, same rule as stg_wb_observations.sql. No
-- joins, no business logic here.

select
    geolocation_name,
    commodity_name,
    cast(year as integer) as year,
    period_name,
    cast(period_num as integer) as period_num,
    cast(cpi_value as double) as cpi_value
from {{ source('raw_psa', 'cpi_observations') }}