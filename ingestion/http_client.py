"""
Shared HTTP concerns for World Bank ingestion: a pooled, retrying session,
and helpers for respecting the API's documented batching syntax and limits.

Why this lives in its own module: connection pooling and retry policy are
cross-cutting concerns, not something that belongs inside a single dlt
resource function. If we add a second data source later (PSA), it should
reuse this same session discipline rather than reinventing it.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# World Bank documents these hard limits on the batching syntax:
# https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
#   - max 60 indicators per call
#   - max 1500 chars between two "/" segments, 4000 chars total in the URL
# We stay well under both by capping batch sizes rather than discovering
# the limit via a 400 error in production.
MAX_COUNTRIES_PER_CALL = 40
MAX_INDICATORS_PER_CALL = 20


def build_session() -> requests.Session:
    """
    A single Session reused across every call in a pipeline run.

    Why this matters for speed: without a shared Session, every
    requests.get() opens a new TCP connection and re-does the TLS
    handshake. Reusing a Session keeps the underlying connection alive
    (HTTP keep-alive) across calls to the same host - this alone is
    typically a bigger win than adding concurrency, because it removes
    fixed per-call overhead rather than just running that overhead in
    parallel.

    The Retry adapter handles transient failures (429 rate-limit, 5xx
    server errors) with exponential backoff, so a single flaky response
    doesn't fail the entire ingestion run.
    """
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=0.5,  # 0.5s, 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
    session.mount("https://", adapter)
    return session


def chunk(items: list, size: int) -> list[list]:
    """Split a list into chunks no larger than `size`. Plain, boring, testable."""
    return [items[i : i + size] for i in range(0, len(items), size)]