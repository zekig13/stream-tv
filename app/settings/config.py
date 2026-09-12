"""Application settings, favorites, and path helpers."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Optional

# Project root: .../stream-tv
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = ROOT_DIR / "cache"
PLAYLIST_CACHE_DIR = CACHE_DIR / "playlists"
LOGO_CACHE_DIR = CACHE_DIR / "logos"
SETTINGS_FILE = DATA_DIR / "settings.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"

DEFAULT_GEOMETRY = "1280x800"
DEFAULT_COUNTRY = "tr"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36 StreamTV/1.0"
)

BASE_URL = "https://publiciptv.com"


class Settings:
    """JSON-backed settings + favorites."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PLAYLIST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {
            "last_country": DEFAULT_COUNTRY,
            "geometry": DEFAULT_GEOMETRY,
            "window_maximized": False,
            "cache_ttl_hours": 12,
        }
        self._favorites: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        with self._lock:
            if SETTINGS_FILE.exists():
                try:
                    loaded = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        self._data.update(loaded)
                except (OSError, json.JSONDecodeError):
                    pass
            if FAVORITES_FILE.exists():
                try:
                    fav = json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
                    if isinstance(fav, list):
                        self._favorites = fav
                except (OSError, json.JSONDecodeError):
                    self._favorites = []

    def save(self) -> None:
        with self._lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            FAVORITES_FILE.write_text(
                json.dumps(self._favorites, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # --- settings accessors ---

    @property
    def last_country(self) -> str:
        return str(self._data.get("last_country") or DEFAULT_COUNTRY).lower()

    @last_country.setter
    def last_country(self, value: str) -> None:
        self._data["last_country"] = (value or DEFAULT_COUNTRY).lower()
        self.save()

    @property
    def geometry(self) -> str:
        return str(self._data.get("geometry") or DEFAULT_GEOMETRY)

    @geometry.setter
    def geometry(self, value: str) -> None:
        self._data["geometry"] = value or DEFAULT_GEOMETRY
        self.save()

    @property
    def window_maximized(self) -> bool:
        return bool(self._data.get("window_maximized", False))

    @window_maximized.setter
    def window_maximized(self, value: bool) -> None:
        self._data["window_maximized"] = bool(value)
        self.save()

    @property
    def cache_ttl_hours(self) -> float:
        try:
            return float(self._data.get("cache_ttl_hours", 12))
        except (TypeError, ValueError):
            return 12.0

    # --- favorites ---

    def get_favorites(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._favorites)

    def is_favorite(self, key: str) -> bool:
        with self._lock:
            return any(self._fav_key(f) == key for f in self._favorites)

    def toggle_favorite(self, channel_dict: dict[str, Any]) -> bool:
        """Add or remove favorite. Returns True if now favorited."""
        key = self._fav_key(channel_dict)
        with self._lock:
            existing = [f for f in self._favorites if self._fav_key(f) != key]
            was = len(existing) != len(self._favorites)
            if was:
                self._favorites = existing
                self.save()
                return False
            self._favorites.append(dict(channel_dict))
            self.save()
            return True

    @staticmethod
    def _fav_key(d: dict[str, Any]) -> str:
        return (
            f"{d.get('country_code', '')}|"
            f"{d.get('tvg_id') or d.get('name', '')}|"
            f"{d.get('url', '')}"
        )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
