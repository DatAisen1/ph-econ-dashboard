"""
Shared HTTP concerns for the PSA OpenSTAT PXWeb API - mirrors
ingestion/http_client.py's approach for World Bank, but adds one thing
World Bank didn't need: a hard rate limiter.

PSA's own API docs (https://openstat.psa.gov.ph/API-Documentation) state:
  "A maximum of 10 requests within 10 seconds is allowed per connection
   or user. Exceeding the allowed request threshold may return an
   HTTP 429 (Too Many Requests) response."

Retry/backoff (from http_client.py's Retry adapter) handles a 429 AFTER
it happens. A rate limiter prevents triggering it in the first place -
the two are complementary, not redundant: one is prevention, one is
recovery from a limit we occasionally still bump into (e.g. if another
process is hitting the same API concurrently).
"""

import time
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PXWEB_BASE = "https://openstat.psa.gov.ph/PXWeb/api/v1/en"


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.0,  # slower backoff than WB's - PSA's limit is stricter
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),  # POST included deliberately -
        # PXWeb's query endpoint is technically a POST, but it's a READ (fetching
        # data, not creating/mutating anything server-side) despite the HTTP verb.
        # Retrying it is safe for the same idempotency reason GET is safe to
        # retry - re-running the same query body returns the same data, it
        # doesn't duplicate anything. Contrast with a "real" POST like
        # submitting a form, which would NOT be safe to blindly retry.
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=5)
    session.mount("https://", adapter)
    return session


class RateLimiter:
    """
    Simple sliding-window limiter: blocks until fewer than `max_calls` have
    happened in the last `period_seconds`. Thread-safe via a lock, since
    Dagster or a future async caller might share one limiter instance.
    """

    def __init__(self, max_calls: int = 10, period_seconds: float = 10.0):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._call_times: list[float] = []
        self._lock = threading.Lock()

    def wait_if_needed(self):
        with self._lock:
            now = time.monotonic()
            self._call_times = [t for t in self._call_times if now - t < self.period_seconds]

            if len(self._call_times) >= self.max_calls:
                sleep_for = self.period_seconds - (now - self._call_times[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                self._call_times = [t for t in self._call_times if now - t < self.period_seconds]

            self._call_times.append(time.monotonic())


# One shared limiter for the whole process - matches PSA's "per connection
# or user" wording, so every call through this module respects the same
# budget rather than each function tracking its own.
psa_rate_limiter = RateLimiter(max_calls=10, period_seconds=10.0)