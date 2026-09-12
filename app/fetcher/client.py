"""Shared HTTP client with polite User-Agent."""

from __future__ import annotations

import time
from typing import Optional

import requests

from app.settings.config import USER_AGENT

_session: Optional[requests.Session] = None
_last_request_at = 0.0
_MIN_INTERVAL = 0.35  # polite pacing between requests


def get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        _session = s
    return _session


def polite_get(url: str, timeout: float = 30.0, **kwargs) -> requests.Response:
    """GET with a small delay between calls to avoid hammering the source."""
    global _last_request_at
    now = time.monotonic()
    wait = _MIN_INTERVAL - (now - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    resp = get_session().get(url, timeout=timeout, **kwargs)
    _last_request_at = time.monotonic()
    return resp
