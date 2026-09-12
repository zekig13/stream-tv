"""Parse M3U playlists embedded in publiciptv.com HTML pages."""

from __future__ import annotations

import html as html_lib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup

from app.fetcher.client import polite_get
from app.models import Channel, Playlist
from app.settings.config import BASE_URL, PLAYLIST_CACHE_DIR, get_settings

EXTINF_RE = re.compile(
    r"#EXTINF\s*:\s*(-?\d+)\s*(.*?)\s*,\s*(.*?)\s*$",
    re.IGNORECASE,
)
ATTR_RE = re.compile(r'([a-zA-Z0-9\-]+)="([^"]*)"')


class M3UParser:
    """Parse #EXTM3U / #EXTINF playlists into Channel objects."""

    @staticmethod
    def parse(text: str, country_code: str = "") -> list[Channel]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # If HTML slipped through, extract <pre> or unescape entities
        if "<pre" in text.lower() or "&quot;" in text or "&#" in text:
            text = M3UParser.extract_from_html(text) or html_lib.unescape(text)

        channels: list[Channel] = []
        lines = [ln.strip() for ln in text.split("\n")]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.upper().startswith("#EXTINF"):
                meta = M3UParser._parse_extinf(line)
                # next non-empty, non-comment line is the URL
                j = i + 1
                url = ""
                while j < len(lines):
                    candidate = lines[j].strip()
                    if not candidate:
                        j += 1
                        continue
                    if candidate.startswith("#"):
                        j += 1
                        continue
                    url = candidate
                    break
                if url:
                    channels.append(
                        Channel(
                            name=meta.get("name") or meta.get("tvg_name") or "Kanal",
                            url=url,
                            tvg_id=meta.get("tvg_id", ""),
                            tvg_name=meta.get("tvg_name", ""),
                            tvg_logo=meta.get("tvg_logo", ""),
                            group_title=meta.get("group_title", ""),
                            country_code=country_code.lower(),
                        )
                    )
                i = j + 1 if url else i + 1
            else:
                i += 1
        return channels

    @staticmethod
    def _parse_extinf(line: str) -> dict[str, str]:
        m = EXTINF_RE.match(line)
        attrs_blob = ""
        display_name = ""
        if m:
            attrs_blob = m.group(2) or ""
            display_name = (m.group(3) or "").strip()
        else:
            # Fallback: everything after first comma
            if "," in line:
                attrs_blob, display_name = line.split(",", 1)
                attrs_blob = attrs_blob.split(":", 1)[-1]
                display_name = display_name.strip()

        attrs = {k.replace("-", "_"): v for k, v in ATTR_RE.findall(attrs_blob)}
        name = display_name or attrs.get("tvg_name") or attrs.get("tvg_id") or "Kanal"
        return {
            "name": name,
            "tvg_id": attrs.get("tvg_id", ""),
            "tvg_name": attrs.get("tvg_name", "") or name,
            "tvg_logo": attrs.get("tvg_logo", ""),
            "group_title": attrs.get("group_title", ""),
        }

    @staticmethod
    def extract_from_html(html: str) -> Optional[str]:
        """Pull M3U text from a <pre> (or similar) on the country M3U page."""
        soup = BeautifulSoup(html, "lxml")
        pre = soup.find("pre")
        if pre is not None:
            raw = pre.get_text()
            raw = html_lib.unescape(raw)
            if "#EXT" in raw.upper():
                return raw

        # Fallback: look for #EXTM3U anywhere in page text
        text = soup.get_text("\n")
        text = html_lib.unescape(text)
        idx = text.upper().find("#EXTM3U")
        if idx >= 0:
            return text[idx:]
        return None


class PlaylistFetcher:
    """Fetch, parse, and cache per-country M3U playlists."""

    def __init__(self, cache_dir: Path = PLAYLIST_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.parser = M3UParser()

    def m3u_url(self, country_code: str) -> str:
        return f"{BASE_URL}/countries/{country_code.lower()}/m3u"

    def get_playlist(
        self, country_code: str, force_refresh: bool = False
    ) -> Playlist:
        code = country_code.lower()
        if not force_refresh:
            cached = self._load_cache(code)
            if cached is not None:
                return cached
        playlist = self.fetch_live(code)
        self._save_cache(playlist)
        return playlist

    def fetch_live(self, country_code: str) -> Playlist:
        code = country_code.lower()
        url = self.m3u_url(code)
        resp = polite_get(url)
        if resp.status_code == 404:
            return Playlist(country_code=code, channels=[], source_url=url)
        resp.raise_for_status()

        content_type = (resp.headers.get("Content-Type") or "").lower()
        body = resp.text

        # Some deployments may serve raw M3U
        if "mpegurl" in content_type or body.lstrip().upper().startswith("#EXTM3U"):
            channels = self.parser.parse(body, country_code=code)
        else:
            extracted = self.parser.extract_from_html(body)
            if not extracted:
                return Playlist(country_code=code, channels=[], source_url=url)
            channels = self.parser.parse(extracted, country_code=code)

        return Playlist(
            country_code=code,
            channels=channels,
            source_url=url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    def _cache_path(self, code: str) -> Path:
        return self.cache_dir / f"{code}.json"

    def _load_cache(self, code: str) -> Optional[Playlist]:
        path = self._cache_path(code)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = payload.get("fetched_at")
            if fetched_at:
                ts = datetime.fromisoformat(fetched_at)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
                if age_h > get_settings().cache_ttl_hours:
                    return None
            channels = [Channel.from_dict(c) for c in payload.get("channels") or []]
            return Playlist(
                country_code=code,
                channels=channels,
                source_url=payload.get("source_url", self.m3u_url(code)),
                fetched_at=fetched_at,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None

    def _save_cache(self, playlist: Playlist) -> None:
        path = self._cache_path(playlist.country_code)
        payload = {
            "fetched_at": playlist.fetched_at
            or datetime.now(timezone.utc).isoformat(),
            "source_url": playlist.source_url,
            "channels": [c.to_dict() for c in playlist.channels],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
