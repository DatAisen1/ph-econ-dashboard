-- Staging: rename/cast ONLY. No joins, no business logic here - that's the
-- rule from Phase 3 planning, and it's enforced by convention, not by dbt
-- itself, so it only holds if we actually follow it. If you ever find
-- yourself tempted to add a JOIN in this file, that's the signal it
-- belongs in marts/ instead.

select
    country_code,
    indicator_code,
    indicator_name,
    cast(year as integer) as year,
    cast(value as double) as value
from {{ source('raw_wb', 'wb_observations') }}