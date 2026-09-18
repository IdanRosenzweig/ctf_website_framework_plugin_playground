"""The stats server, as CTFd talks to it.

One ``StatsClient`` per application: it knows the server's address, fetches
``GET /stats?window=...`` with a timeout, and remembers each answer - and each
failure - for a short while so that a page full of viewers polling every few
seconds turns into a trickle of requests upstream.
"""

import threading
import time

import requests


class StatsUnavailable(Exception):
    """The stats server could not be asked, or did not answer with stats."""


class StatsClient:
    def __init__(self, url, timeout, ttl, clock=time.monotonic):
        self.url = url.rstrip("/") + "/stats"
        self.timeout = timeout
        self.ttl = ttl
        self.clock = clock
        self._lock = threading.Lock()
        # window -> (expires_at, stats dict or StatsUnavailable)
        self._cache = {}

    def get(self, window=None):
        """The stats for ``window`` (the server's default when None).

        Raises StatsUnavailable when the server cannot be reached, does not
        answer in time, or answers with something other than stats. A cached
        failure is raised again until it expires, so a server that is down is
        not asked once per viewer per refresh.
        """
        with self._lock:
            cached = self._cache.get(window)
            if cached is not None and cached[0] > self.clock():
                result = cached[1]
            else:
                result = self._fetch(window)
                self._cache[window] = (self.clock() + self.ttl, result)

        if isinstance(result, StatsUnavailable):
            raise result
        return result

    def fetch(self, window=None):
        """The stats for ``window`` straight from the server, bypassing the cache."""
        result = self._fetch(window)
        if isinstance(result, StatsUnavailable):
            raise result
        return result

    def clear(self):
        with self._lock:
            self._cache.clear()

    def _fetch(self, window):
        params = {"window": window} if window else None
        try:
            response = requests.get(self.url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            return StatsUnavailable(f"{self.url}: {describe(exc)}")

        try:
            body = response.json()
        except ValueError:
            return StatsUnavailable(
                f"{self.url}: http {response.status_code} with a body that is not json"
            )

        if response.status_code != 200 or not isinstance(body, dict):
            detail = body.get("error") if isinstance(body, dict) else None
            return StatsUnavailable(
                f"{self.url}: http {response.status_code}"
                + (f" ({detail})" if detail else "")
            )

        if "currently_connected" not in body:
            return StatsUnavailable(f"{self.url}: the answer is not playground stats")

        return body


def describe(exc):
    """A requests exception in a line: the innermost cause, not the wrapper."""
    if isinstance(exc, requests.Timeout):
        return "timed out"
    if isinstance(exc, requests.ConnectionError):
        return "connection refused or host unreachable"
    return f"{type(exc).__name__}: {exc}"
