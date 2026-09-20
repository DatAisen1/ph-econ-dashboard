-- Thin pass-through over the seed. Why not just reference the seed
-- directly from fact_country_comparison.sql? Because "dim_country" should
-- be a stable interface - if we later replace the CSV seed with a live
-- pull from WB's /country endpoint (Phase 6 hardening candidate), only
-- this one file changes. Every downstream model keeps working unchanged.

select
    country_code,
    country_name,
    region,
    income_group
from {{ ref('seed_country_reference') }}