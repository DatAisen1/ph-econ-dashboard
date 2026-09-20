import pandas as pd
from transform import clean_observations, enrich_with_country_dim

RAW_FIXTURE = pd.DataFrame([
    {"country_code": "PHL", "country_name": "Philippines", "indicator_code": "NY.GDP.MKTP.CD",
     "indicator_name": "gdp_current_usd", "year": "2023", "value": 437147404860.9, "unit": None},
    {"country_code": "IDN", "country_name": "Indonesia", "indicator_code": "NY.GDP.MKTP.CD",
     "indicator_name": "gdp_current_usd", "year": "2021", "value": None, "unit": None},  # real WB gap
])

DIM_COUNTRY_FIXTURE = pd.DataFrame([
    {"country_code": "PHL", "country_name": "Philippines", "region": "East Asia & Pacific",
     "income_group": "Lower middle income"},
    {"country_code": "IDN", "country_name": "Indonesia", "region": "East Asia & Pacific",
     "income_group": "Upper middle income"},
])


def test_clean_observations_casts_types_and_preserves_nulls():
    result = clean_observations(RAW_FIXTURE)
    assert result["year"].dtype == "int64"
    assert pd.api.types.is_numeric_dtype(result["value"])
    # the null value for IDN/2021 must survive the cast, not become 0 or vanish
    idn_row = result[(result["country_code"] == "IDN") & (result["year"] == 2021)]
    assert idn_row["value"].isna().all()


def test_enrich_joins_known_country_correctly():
    staged = clean_observations(RAW_FIXTURE)
    enriched = enrich_with_country_dim(staged, DIM_COUNTRY_FIXTURE)
    phl_row = enriched[enriched["country_code"] == "PHL"].iloc[0]
    assert phl_row["region"] == "East Asia & Pacific"
    assert phl_row["income_group"] == "Lower middle income"


def test_enrich_left_join_survives_unknown_country():
    """
    The exact scenario the docstring warns about: a country not present in
    the seed must still produce a row, with null dimension columns, NOT
    silently disappear.
    """
    staged = clean_observations(RAW_FIXTURE)
    # simulate a country the seed doesn't know about yet
    staged.loc[len(staged)] = ["MYS", "NY.GDP.MKTP.CD", "gdp_current_usd", 2023, 123.0]

    enriched = enrich_with_country_dim(staged, DIM_COUNTRY_FIXTURE)

    assert len(enriched) == 3  # MYS row survived
    mys_row = enriched[enriched["country_code"] == "MYS"].iloc[0]
    assert pd.isna(mys_row["region"])  # visibly incomplete, not silently dropped


if __name__ == "__main__":
    test_clean_observations_casts_types_and_preserves_nulls()
    test_enrich_joins_known_country_correctly()
    test_enrich_left_join_survives_unknown_country()
    print("PASSED: 3/3 staging transform tests")