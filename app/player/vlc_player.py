"""VLC-based playback with Turkish fallbacks when VLC is missing."""

from __future__ import annotations

import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from typing import Optional

from app.models import Channel

VLC_AVAILABLE = False
_vlc = None

try:
    import vlc as _vlc_mod  # type: ignore

    # Probe that libvlc is actually loadable
    try:
        _inst = _vlc_mod.Instance("--quiet")
        if _inst is not None:
            VLC_AVAILABLE = True
            _vlc = _vlc_mod
        del _inst
    except Exception:
        VLC_AVAILABLE = False
        _vlc = None
except Exception:
    VLC_AVAILABLE = False
    _vlc = None


VLC_MISSING_TR = (
    "VLC Media Player bulunamadı.\n\n"
    "Yayını izlemek için VLC'yi kurun:\n"
    "https://www.videolan.org/vlc/\n\n"
    "Kurulumdan sonra Stream TV'yi yeniden başlatın.\n"
    "Şimdilik URL'yi tarayıcıda açabilir veya panoya kopyalayabilirsiniz."
)


@dataclass
class PlayResult:
    ok: bool
    message: str = ""
    used_vlc: bool = False
    opened_browser: bool = False


class PlayerController:
    """Play IPTV streams via python-vlc, or fall back to OS / browser."""

    def __init__(self) -> None:
        self._instance = None
        self._player = None
        self._current: Optional[Channel] = None
        if VLC_AVAILABLE and _vlc is not None:
            try:
                self._instance = _vlc.Instance(
                    "--quiet",
                    "--no-video-title-show",
                    "--network-caching=1000",
                )
                self._player = self._instance.media_player_new()
            except Exception:
                self._instance = None
                self._player = None

    @property
    def vlc_ready(self) -> bool:
        return self._player is not None

    @property
    def current_channel(self) -> Optional[Channel]:
        return self._current

    def play(self, channel: Channel) -> PlayResult:
        self._current = channel
        if self._player is not None and self._instance is not None and _vlc is not None:
            try:
                media = self._instance.media_new(channel.url)
                self._player.set_media(media)
                self._player.play()
                return PlayResult(
                    ok=True,
                    message=f"Oynatılıyor: {channel.display_name}",
                    used_vlc=True,
                )
            except Exception as exc:
                return PlayResult(
                    ok=False,
                    message=f"VLC oynatma hatası: {exc}",
                    used_vlc=False,
                )
        return PlayResult(ok=False, message=VLC_MISSING_TR, used_vlc=False)

    def stop(self) -> None:
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass

    def pause(self) -> None:
        if self._player is not None:
            try:
                self._player.pause()
            except Exception:
                pass

    def is_playing(self) -> bool:
        if self._player is None:
            return False
        try:
            return bool(self._player.is_playing())
        except Exception:
            return False

    def open_in_browser(self, url: str) -> PlayResult:
        try:
            webbrowser.open(url)
            return PlayResult(ok=True, message="Tarayıcıda açıldı.", opened_browser=True)
        except Exception as exc:
            return PlayResult(ok=False, message=f"Tarayıcı açılamadı: {exc}")

    def open_in_system_vlc(self, url: str) -> PlayResult:
        """Try launching the VLC executable directly (Windows/Linux)."""
        candidates = []
        if sys.platform.startswith("win"):
            candidates.extend(
                [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                ]
            )
        which = shutil.which("vlc")
        if which:
            candidates.insert(0, which)
        for exe in candidates:
            try:
                subprocess.Popen([exe, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return PlayResult(ok=True, message="Sistem VLC ile açıldı.", used_vlc=True)
            except OSError:
                continue
        return PlayResult(ok=False, message=VLC_MISSING_TR)

    def release(self) -> None:
        self.stop()
        self._player = None
        self._instance = None
