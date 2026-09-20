-- PSA CPI detail at geolocation, commodity, year, and month grain.

select
	geolocation_name,
	commodity_name,
	year,
	period_name,
	period_num,
	cpi_value
from {{ ref('stg_psa_cpi') }}
