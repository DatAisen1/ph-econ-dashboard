import pandas as pd
from transform_export import build_country_comparison_json, build_ph_commodity_json, build_ph_detail_json

PH_DETAIL_FIXTURE = pd.DataFrame([
    {"geolocation_name": "PHILIPPINES", "year": 2018, "period_num": 1, "cpi_value": 97.2},
    {"geolocation_name": "..National Capital Region (NCR)", "year": 2018, "period_num": 1, "cpi_value": 96.9},
    {"geolocation_name": "PHILIPPINES", "year": 2018, "period_num": 2, "cpi_value": 97.9},
    # NCR/Feb deliberately missing - a real gap PSA sometimes has
])

COUNTRY_FIXTURE = pd.DataFrame([
    {"country_code": "PHL", "indicator_code": "NY.GDP.MKTP.CD", "indicator_name": "gdp_current_usd", "year": 2022, "value": 404284226539.1},
    {"country_code": "IDN", "indicator_code": "NY.GDP.MKTP.CD", "indicator_name": "gdp_current_usd", "year": 2022, "value": 1319100000000.0},
    {"country_code": "PHL", "indicator_code": "FP.CPI.TOTL.ZG", "indicator_name": "inflation_cpi_annual_pct", "year": 2022, "value": 5.8},
])

COMMODITY_FIXTURE = pd.DataFrame([
    {"geolocation_name": "PHILIPPINES", "commodity_name": "01 - FOOD", "year": 2025, "period_num": 1, "cpi_value": 128.4},
    {"geolocation_name": "PHILIPPINES", "commodity_name": "07 - TRANSPORT", "year": 2025, "period_num": 1, "cpi_value": 135.2},
])


def test_ph_detail_pivots_to_wide_and_sorts_chronologically():
    result = build_ph_detail_json(PH_DETAIL_FIXTURE)
    assert [r["date"] for r in result] == ["2018-01", "2018-02"]


def test_ph_detail_preserves_missing_value_as_null_not_zero():
    result = build_ph_detail_json(PH_DETAIL_FIXTURE)
    feb_row = [r for r in result if r["date"] == "2018-02"][0]
    assert feb_row["PHILIPPINES"] == 97.9
    assert feb_row["National Capital Region (NCR)"] is None  # must be null, NOT 0.0 or dropped entirely


def test_ph_detail_normalizes_leading_dots_from_pxweb_labels():
    """
    PXWeb labels regions with leading dots as a hierarchy indicator
    (".." for region-level). That must NOT leak into the JSON keys the
    frontend consumes.
    """
    result = build_ph_detail_json(PH_DETAIL_FIXTURE)
    jan_row = result[0]
    assert "National Capital Region (NCR)" in jan_row
    assert "..National Capital Region (NCR)" not in jan_row
    assert jan_row["National Capital Region (NCR)"] == 96.9


def test_ph_detail_raises_on_unfiltered_multi_commodity_data():
    """
    The exact bug this project hit for real: if the caller forgets to
    filter to one commodity before calling build_ph_detail_json, there
    are multiple rows per (date, geolocation) - this must raise loudly,
    not silently pick one via pivot_table's aggfunc="first".
    """
    unfiltered = pd.DataFrame([
        {"geolocation_name": "PHILIPPINES", "year": 2018, "period_num": 1, "cpi_value": 97.2},  # ALL ITEMS
        {"geolocation_name": "PHILIPPINES", "year": 2018, "period_num": 1, "cpi_value": 88.5},  # Food (different commodity, same date/geo!)
    ])
    try:
        build_ph_detail_json(unfiltered)
        assert False, "expected ValueError for duplicate (date, geolocation) rows, but none was raised"
    except ValueError as e:
        assert "one row per" in str(e)


def test_country_comparison_groups_by_indicator():
    result = build_country_comparison_json(COUNTRY_FIXTURE)
    assert set(result.keys()) == {"NY.GDP.MKTP.CD", "FP.CPI.TOTL.ZG"}
    assert result["NY.GDP.MKTP.CD"]["indicator_name"] == "gdp_current_usd"


def test_country_comparison_series_is_wide_per_year():
    result = build_country_comparison_json(COUNTRY_FIXTURE)
    gdp_series = result["NY.GDP.MKTP.CD"]["series"]
    assert len(gdp_series) == 1  # one year (2022) in the fixture
    row = gdp_series[0]
    assert row["PHL"] == 404284226539.1
    assert row["IDN"] == 1319100000000.0


def test_ph_commodity_pivots_by_date_and_geography():
    result = build_ph_commodity_json(COMMODITY_FIXTURE)
    assert result == [{
        "date": "2025-01",
        "geolocation_name": "PHILIPPINES",
        "01 - FOOD": 128.4,
        "07 - TRANSPORT": 135.2,
    }]


if __name__ == "__main__":
    test_ph_detail_pivots_to_wide_and_sorts_chronologically()
    test_ph_detail_preserves_missing_value_as_null_not_zero()
    test_ph_detail_normalizes_leading_dots_from_pxweb_labels()
    test_ph_detail_raises_on_unfiltered_multi_commodity_data()
    test_country_comparison_groups_by_indicator()
    test_country_comparison_series_is_wide_per_year()
    test_ph_commodity_pivots_by_date_and_geography()
    print("PASSED: 7/7 export transform tests")