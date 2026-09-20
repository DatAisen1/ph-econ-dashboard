"""
dlt source for the World Bank Indicators API - speed-optimized version.

REFACTOR SUMMARY (see the mentor conversation for the full reasoning):

1. Countries are batched into one request via the documented `A;B;C` syntax
   instead of one request per country. For 5 countries x 5 indicators, this
   takes call count from 25 down to 5 - a real reduction in work, not just
   the same work spread across threads.

2. We ALSO attempt to batch indicators into that same call (`source=2` lets
   WB return multiple indicators at once), which would take 5 calls down to
   1. This part is DEFENSIVE: I could not fully verify this path against
   the live API from my side, so it's wrapped in a try/except that falls
   back to the safer per-indicator (but still country-batched) path if the
   combined call fails for any reason. Never ship an unverified fast path
   without a verified fallback.

3. All requests reuse one pooled, retrying Session (see http_client.py)
   instead of opening a fresh connection per call.

4. Destination changed from 5 separate per-indicator tables to ONE shared
   `wb_observations` table, with indicator_code as a column. This is the
   fact-table shape we actually want for the dbt star schema in Phase 3 -
   dimensional modeling and performance improvement happened to point the
   same direction here.
"""

import dlt
from http_client import build_session, chunk, MAX_COUNTRIES_PER_CALL

WB_BASE_URL = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicators}"

_session = build_session()


def _parse_records(records: list[dict], indicator_names: dict[str, str]):
    for r in records:
        indicator_code = r["indicator"]["id"]
        yield {
            "country_code": r["countryiso3code"],
            "country_name": r["country"]["value"],
            "indicator_code": indicator_code,
            "indicator_name": indicator_names.get(indicator_code, indicator_code),
            "year": int(r["date"]),
            "value": r["value"],  # can be None - WB has real gaps, never drop silently
            "unit": r.get("unit") or None,
        }


def _fetch_all_pages(country_batch: str, indicator_param: str, extra_params: dict) -> list[dict]:
    """One (possibly multi-country, possibly multi-indicator) query, fully paginated."""
    records = []
    page = 1
    while True:
        resp = _session.get(
            WB_BASE_URL.format(countries=country_batch, indicators=indicator_param),
            params={**extra_params, "format": "json", "per_page": 1000, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        # WB returns a bare error dict (not the usual [meta, records] list)
        # on some invalid parameter combinations. Treat that as a failure
        # so the caller's fallback logic kicks in, instead of crashing on
        # "cannot unpack non-iterable dict".
        if isinstance(payload, dict):
            raise ValueError(f"WB API returned an error payload: {payload}")

        meta, page_records = payload
        if not page_records:
            break
        records.extend(page_records)

        if page >= meta["pages"]:
            break
        page += 1

    return records


@dlt.resource(name="wb_observations", write_disposition="replace")
def wb_observations(countries: list[str], indicators: dict[str, str]):
    """
    Yields flat (country, indicator, year) observation rows for every
    country x indicator combination, batching HTTP calls as aggressively
    as the API allows.
    """
    indicator_codes = list(indicators.keys())
    country_batches = chunk(countries, MAX_COUNTRIES_PER_CALL)

    for country_batch in country_batches:
        country_param = ";".join(country_batch)

        # FAST PATH: try all indicators in one call for this country batch.
        try:
            records = _fetch_all_pages(
                country_param,
                ";".join(indicator_codes),
                extra_params={"source": 2},
            )
            yield from _parse_records(records, indicators)
            continue  # this country batch is done, move to the next
        except Exception as exc:
            print(
                f"[wb_observations] combined indicator batch failed "
                f"({exc!r}); falling back to per-indicator calls for "
                f"countries={country_param}"
            )

        # FALLBACK PATH: one call per indicator, still country-batched.
        # Still 5 calls instead of 25 for our current indicator set - the
        # country-batching win survives even if indicator-batching doesn't.
        for indicator_code in indicator_codes:
            records = _fetch_all_pages(country_param, indicator_code, extra_params={})
            yield from _parse_records(records, indicators)


@dlt.source
def worldbank_source(countries: list[str], indicators: dict[str, str]):
    yield wb_observations(countries, indicators)


# --- Why "replace", not "append", for this table ---
# The World Bank re-publishes revised figures for past years under the SAME
# (country, indicator, year) key. If we used "append", every run would add a
# new duplicate row for e.g. PHL/2020 instead of updating it - you'd end up
# with 2, 3, 10 rows for the same fact after 10 daily runs, and no way to
# tell which one is "current" without extra logic.
#
# "merge" (upsert on a primary key) would actually be the MOST correct
# choice in a mature pipeline - it updates existing (country, indicator,
# year) rows and inserts new ones, without wiping history you might want to
# diff against. We're using "replace" for now because it's simpler to reason
# about while you're learning, and the WB dataset is small enough that a
# full reload costs nothing. Upgrading to "merge" with a composite primary
# key is a good Phase 6 hardening exercise.