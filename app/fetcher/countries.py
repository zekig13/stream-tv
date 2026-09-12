"""Fetch and cache country list from publiciptv.com/countries."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from app.fetcher.client import polite_get
from app.models import Country
from app.settings.config import BASE_URL, CACHE_DIR, get_settings

COUNTRIES_URL = f"{BASE_URL}/countries"
COUNTRIES_CACHE = CACHE_DIR / "countries.json"


class CountryFetcher:
    """Scrapes country cards: flag, name, counts, and M3U availability."""

    def __init__(self, cache_path: Path = COUNTRIES_CACHE) -> None:
        self.cache_path = cache_path

    def get_countries(self, force_refresh: bool = False) -> list[Country]:
        if not force_refresh:
            cached = self._load_cache()
            if cached is not None:
                return cached
        countries = self.fetch_live()
        self._save_cache(countries)
        return countries

    def fetch_live(self) -> list[Country]:
        resp = polite_get(COUNTRIES_URL)
        resp.raise_for_status()
        return self.parse_html(resp.text)

    @staticmethod
    def parse_html(html: str) -> list[Country]:
        soup = BeautifulSoup(html, "lxml")
        by_code: dict[str, Country] = {}

        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.match(r"^/countries/([a-z]{2})$", href)
            if not m:
                continue
            code = m.group(1)

            # Prefer the main country link that contains the name span
            flag = ""
            name = code.upper()
            channel_count = 0
            stream_count = 0

            text = a.get_text(" ", strip=True)
            # Extract emoji flag (usually first grapheme cluster-ish)
            flag_m = re.match(r"^(\S+)\s+(.*)$", text)
            if flag_m:
                maybe_flag, rest = flag_m.group(1), flag_m.group(2)
                if any(ord(ch) > 127 for ch in maybe_flag):
                    flag = maybe_flag
                    text = rest

            # Name + optional "(channels / streams)"
            count_m = re.search(r"\(\s*(\d+)\s*/\s*(\d+)\s*\)\s*$", text)
            if count_m:
                channel_count = int(count_m.group(1))
                stream_count = int(count_m.group(2))
                name = text[: count_m.start()].strip()
            else:
                name = text.strip() or code.upper()

            # Clean HTML comment leftovers
            name = re.sub(r"\s+", " ", name).strip() or code.upper()

            # Check sibling / nearby "Get M3U" link
            has_m3u = True
            parent = a.parent
            if parent is not None:
                m3u_link = parent.find("a", href=f"/countries/{code}/m3u")
                if m3u_link is None and parent.parent is not None:
                    m3u_link = parent.parent.find("a", href=f"/countries/{code}/m3u")
                # If page lists countries without M3U button, still try later
                has_m3u = m3u_link is not None or channel_count > 0

            country = Country(
                code=code,
                name=name,
                flag=flag,
                channel_count=channel_count,
                stream_count=stream_count,
                has_m3u=has_m3u,
            )
            # Keep richer entry if we see the card again
            prev = by_code.get(code)
            if prev is None or (country.name and len(country.name) >= len(prev.name)):
                by_code[code] = country

        countries = sorted(by_code.values(), key=lambda c: c.name.casefold())
        return countries

    def _load_cache(self) -> Optional[list[Country]]:
        if not self.cache_path.exists():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            fetched_at = payload.get("fetched_at")
            if fetched_at:
                ts = datetime.fromisoformat(fetched_at)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
                if age_h > get_settings().cache_ttl_hours:
                    return None
            items = payload.get("countries") or []
            return [Country.from_dict(x) for x in items]
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None

    def _save_cache(self, countries: list[Country]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "countries": [c.to_dict() for c in countries],
        }
        self.cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
