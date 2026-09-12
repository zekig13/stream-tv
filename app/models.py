"""Domain models for Stream TV."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass(slots=True)
class Country:
    """A country with an optional M3U playlist on publiciptv.com."""

    code: str  # ISO 3166-1 alpha-2, lowercase
    name: str
    flag: str = ""
    channel_count: int = 0
    stream_count: int = 0
    has_m3u: bool = True

    @property
    def display_name(self) -> str:
        prefix = f"{self.flag} " if self.flag else ""
        return f"{prefix}{self.name}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Country":
        return cls(
            code=str(data.get("code", "")).lower(),
            name=str(data.get("name", "")),
            flag=str(data.get("flag", "")),
            channel_count=int(data.get("channel_count", 0) or 0),
            stream_count=int(data.get("stream_count", 0) or 0),
            has_m3u=bool(data.get("has_m3u", True)),
        )


@dataclass(slots=True)
class Channel:
    """A single IPTV channel from an M3U playlist."""

    name: str
    url: str
    tvg_id: str = ""
    tvg_name: str = ""
    tvg_logo: str = ""
    group_title: str = ""
    country_code: str = ""

    @property
    def category(self) -> str:
        return (self.group_title or "").strip() or "Diğer"

    @property
    def display_name(self) -> str:
        return (self.tvg_name or self.name or self.tvg_id or "Kanal").strip()

    @property
    def favorite_key(self) -> str:
        """Stable key for favorites persistence."""
        return f"{self.country_code}|{self.tvg_id or self.name}|{self.url}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Channel":
        return cls(
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            tvg_id=str(data.get("tvg_id", "")),
            tvg_name=str(data.get("tvg_name", "")),
            tvg_logo=str(data.get("tvg_logo", "")),
            group_title=str(data.get("group_title", "")),
            country_code=str(data.get("country_code", "")),
        )


@dataclass
class Playlist:
    """Parsed M3U playlist for one country."""

    country_code: str
    channels: list[Channel] = field(default_factory=list)
    source_url: str = ""
    fetched_at: Optional[str] = None

    @property
    def categories(self) -> list[str]:
        cats = sorted({c.category for c in self.channels})
        return cats
