-- LEFT JOIN, not INNER - same reasoning as staging/transform.py in Phase 2.
-- If a country in stg_wb_observations has no match in dim_country (seed
-- not yet updated for a newly-added country), that row must still appear
-- here - with null region/income_group - so the relationships test in
-- schema.yml has something to actually catch. An INNER join would make
-- that row disappear before dbt test ever got a chance to see it.

select
    obs.country_code,
    dim.country_name,
    dim.region,
    dim.income_group,
    obs.indicator_code,
    obs.indicator_name,
    obs.year,
    obs.value
from {{ ref('stg_wb_observations') }} as obs
left join {{ ref('dim_country') }} as dim
    on obs.country_code = dim.country_code