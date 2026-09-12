"""Main Stream TV window — dark premium media UI."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from app.fetcher.countries import CountryFetcher
from app.fetcher.m3u_parser import PlaylistFetcher
from app.models import Channel, Country
from app.player.vlc_player import VLC_AVAILABLE, PlayerController, VLC_MISSING_TR
from app.settings.config import get_settings
from app.ui import theme as T
from app.ui.channel_panel import ChannelPanel
from app.ui.country_panel import CountryPanel
from app.ui.widgets import StatusBar
from app.version import APP_NAME, __version__


class StreamTVApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.settings = get_settings()
        self.country_fetcher = CountryFetcher()
        self.playlist_fetcher = PlaylistFetcher()
        self.player = PlayerController()

        self._countries: list[Country] = []
        self._current_country: Optional[Country] = None
        self._current_channels: list[Channel] = []
        self._loading = False

        self._configure_window()
        self._build_ui()
        self.after(100, self._bootstrap)

    # ------------------------------------------------------------------ UI
    def _configure_window(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title(f"{APP_NAME} v{__version__}")
        self.configure(fg_color=T.BG_ROOT)
        try:
            self.geometry(self.settings.geometry)
        except Exception:
            self.geometry("1280x800")
        self.minsize(960, 600)
        if self.settings.window_maximized:
            try:
                self.state("zoomed")
            except Exception:
                pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        # Top brand bar
        top = ctk.CTkFrame(self, fg_color=T.BG_SIDEBAR, height=56, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        brand = ctk.CTkLabel(
            top,
            text=f"◈  {APP_NAME}",
            font=(T.FONT_FAMILY, 18, "bold"),
            text_color=T.TEXT_ACCENT,
        )
        brand.pack(side="left", padx=18)

        subtitle = ctk.CTkLabel(
            top,
            text="Ücretsiz IPTV • publiciptv.com",
            font=T.FONT_SMALL,
            text_color=T.TEXT_DIM,
        )
        subtitle.pack(side="left", padx=8)

        self.vlc_badge = ctk.CTkLabel(
            top,
            text="VLC hazır" if (VLC_AVAILABLE and self.player.vlc_ready) else "VLC yok",
            font=T.FONT_SMALL,
            text_color=T.SUCCESS if (VLC_AVAILABLE and self.player.vlc_ready) else T.WARNING,
        )
        self.vlc_badge.pack(side="right", padx=18)

        self.now_playing = ctk.CTkLabel(
            top,
            text="",
            font=T.FONT_BODY,
            text_color=T.TEXT_MUTED,
        )
        self.now_playing.pack(side="right", padx=8)

        # Body
        body = ctk.CTkFrame(self, fg_color=T.BG_ROOT, corner_radius=0)
        body.pack(fill="both", expand=True)

        self.country_panel = CountryPanel(
            body,
            on_select=self._on_country_selected,
            on_refresh=self._refresh_countries,
        )
        self.country_panel.pack(side="left", fill="y")

        # subtle divider
        divider = ctk.CTkFrame(body, width=1, fg_color=T.BORDER, corner_radius=0)
        divider.pack(side="left", fill="y")

        right = ctk.CTkFrame(body, fg_color=T.BG_ROOT, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        self.channel_panel = ChannelPanel(
            right,
            on_play=self._on_play_channel,
            on_favorite_changed=self._on_favorite_view_changed,
        )
        self.channel_panel.pack(fill="both", expand=True)

        # Playback bar
        playbar = ctk.CTkFrame(self, fg_color=T.BG_ELEVATED, height=52, corner_radius=0)
        playbar.pack(fill="x")
        playbar.pack_propagate(False)

        self.stop_btn = ctk.CTkButton(
            playbar,
            text="⏹ Durdur",
            width=100,
            height=34,
            fg_color=T.BG_CARD,
            hover_color=T.DANGER,
            command=self._stop_playback,
        )
        self.stop_btn.pack(side="left", padx=14, pady=8)

        self.open_url_btn = ctk.CTkButton(
            playbar,
            text="Tarayıcıda Aç",
            width=120,
            height=34,
            fg_color=T.BG_CARD,
            hover_color=T.ACCENT,
            command=self._open_current_in_browser,
        )
        self.open_url_btn.pack(side="left", padx=4, pady=8)

        self.copy_url_btn = ctk.CTkButton(
            playbar,
            text="URL Kopyala",
            width=110,
            height=34,
            fg_color=T.BG_CARD,
            hover_color=T.ACCENT,
            command=self._copy_current_url,
        )
        self.copy_url_btn.pack(side="left", padx=4, pady=8)

        self.system_vlc_btn = ctk.CTkButton(
            playbar,
            text="Sistem VLC",
            width=110,
            height=34,
            fg_color=T.BG_CARD,
            hover_color=T.ACCENT,
            command=self._open_current_in_system_vlc,
        )
        self.system_vlc_btn.pack(side="left", padx=4, pady=8)

        self.play_status = ctk.CTkLabel(
            playbar,
            text="Bir kanal seçin",
            font=T.FONT_BODY,
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.play_status.pack(side="left", padx=16, fill="x", expand=True)

        self.status = StatusBar(self)
        self.status.pack(fill="x")

    # -------------------------------------------------------------- bootstrap
    def _bootstrap(self) -> None:
        self.status.set_text("Ülkeler yükleniyor…")
        threading.Thread(target=self._load_countries_worker, daemon=True).start()

    def _load_countries_worker(self, force: bool = False) -> None:
        try:
            countries = self.country_fetcher.get_countries(force_refresh=force)
            self.after(0, lambda: self._on_countries_loaded(countries))
        except Exception as exc:
            self.after(0, lambda: self._on_countries_error(exc))

    def _on_countries_loaded(self, countries: list[Country]) -> None:
        self._countries = countries
        code = self.settings.last_country
        self.country_panel.set_countries(countries, select_code=code)
        self.status.set_text(f"{len(countries)} ülke yüklendi", T.SUCCESS)

    def _on_countries_error(self, exc: Exception) -> None:
        self.status.set_text(f"Ülkeler alınamadı: {exc}", T.DANGER)
        messagebox.showerror(
            "Bağlantı Hatası",
            f"Ülke listesi indirilemedi.\n\n{exc}\n\nİnternet bağlantınızı kontrol edin.",
        )

    def _refresh_countries(self) -> None:
        if self._loading:
            return
        self.status.set_text("Ülkeler yenileniyor…")
        threading.Thread(
            target=self._load_countries_worker, kwargs={"force": True}, daemon=True
        ).start()

    # -------------------------------------------------------------- country
    def _on_country_selected(self, country: Country) -> None:
        if self._loading and self._current_country and self._current_country.code == country.code:
            return
        self._current_country = country
        self.settings.last_country = country.code
        # Exit favorites-only view when picking a country
        if self.channel_panel.favorites_only:
            self.channel_panel.set_favorites_only(False)
        self.status.set_text(f"{country.display_name} kanalları yükleniyor…")
        self.channel_panel.set_title(f"{country.display_name} — yükleniyor…")
        self._loading = True
        threading.Thread(
            target=self._load_playlist_worker,
            args=(country.code, country.name),
            daemon=True,
        ).start()

    def _load_playlist_worker(self, code: str, name: str, force: bool = False) -> None:
        try:
            playlist = self.playlist_fetcher.get_playlist(code, force_refresh=force)
            self.after(
                0,
                lambda: self._on_playlist_loaded(code, name, playlist.channels),
            )
        except Exception as exc:
            self.after(0, lambda: self._on_playlist_error(name, exc))

    def _on_playlist_loaded(
        self, code: str, name: str, channels: list[Channel]
    ) -> None:
        self._loading = False
        if self._current_country and self._current_country.code != code:
            return  # stale
        self._current_channels = channels
        if not channels:
            self.channel_panel.set_channels([], country_name=name)
            self.status.set_text(
                f"{name}: M3U bulunamadı veya kanal yok",
                T.WARNING,
            )
            return
        self.channel_panel.set_channels(channels, country_name=f"{name}")
        self.status.set_text(f"{name}: {len(channels)} kanal", T.SUCCESS)

    def _on_playlist_error(self, name: str, exc: Exception) -> None:
        self._loading = False
        self.status.set_text(f"{name} yüklenemedi: {exc}", T.DANGER)
        messagebox.showwarning(
            "Playlist Hatası",
            f"{name} için M3U alınamadı.\n\n{exc}",
        )

    # -------------------------------------------------------------- playback
    def _on_play_channel(self, channel: Channel) -> None:
        result = self.player.play(channel)
        if result.ok and result.used_vlc:
            self.play_status.configure(
                text=f"▶  {channel.display_name}",
                text_color=T.SUCCESS,
            )
            self.now_playing.configure(text=channel.display_name)
            self.status.set_text(result.message, T.SUCCESS)
            return

        # Prefer launching installed VLC.exe before showing the dialog
        sys_result = self.player.open_in_system_vlc(channel.url)
        if sys_result.ok:
            self.play_status.configure(
                text=f"▶  {channel.display_name} (VLC)",
                text_color=T.SUCCESS,
            )
            self.now_playing.configure(text=channel.display_name)
            self.status.set_text(sys_result.message, T.SUCCESS)
            return

        self.play_status.configure(text=channel.display_name, text_color=T.WARNING)
        self.now_playing.configure(text=channel.display_name)
        choice = messagebox.askyesnocancel(
            "VLC Gerekli",
            f"{VLC_MISSING_TR}\n\n"
            f"Kanal: {channel.display_name}\n\n"
            "Evet = Tarayıcıda aç\n"
            "Hayır = URL'yi panoya kopyala\n"
            "İptal = Vazgeç",
        )
        if choice is True:
            self.player.open_in_browser(channel.url)
            self.status.set_text("Tarayıcıda açıldı", T.WARNING)
        elif choice is False:
            self._copy_url(channel.url)
        else:
            self.status.set_text("Oynatma iptal edildi", T.TEXT_MUTED)

    def _stop_playback(self) -> None:
        self.player.stop()
        self.play_status.configure(text="Durduruldu", text_color=T.TEXT_MUTED)
        self.now_playing.configure(text="")
        self.status.set_text("Oynatma durduruldu")

    def _open_current_in_browser(self) -> None:
        ch = self.player.current_channel
        if not ch:
            self.status.set_text("Önce bir kanal seçin", T.WARNING)
            return
        self.player.open_in_browser(ch.url)
        self.status.set_text("Tarayıcıda açıldı", T.SUCCESS)


    def _open_current_in_system_vlc(self) -> None:
        ch = self.player.current_channel
        if not ch:
            self.status.set_text("Önce bir kanal seçin", T.WARNING)
            return
        result = self.player.open_in_system_vlc(ch.url)
        if result.ok:
            self.now_playing.configure(text=ch.display_name)
            self.play_status.configure(
                text=f"▶  {ch.display_name} (VLC)",
                text_color=T.SUCCESS,
            )
            self.status.set_text(result.message, T.SUCCESS)
        else:
            self.status.set_text(result.message, T.WARNING)
            messagebox.showinfo("VLC", VLC_MISSING_TR)

    def _copy_current_url(self) -> None:
        ch = self.player.current_channel
        if not ch:
            self.status.set_text("Önce bir kanal seçin", T.WARNING)
            return
        self._copy_url(ch.url)

    def _copy_url(self, url: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.status.set_text("URL panoya kopyalandı", T.SUCCESS)
        except tk.TclError:
            self.status.set_text("Pano kullanılamadı", T.DANGER)

    # -------------------------------------------------------------- favorites
    def _on_favorite_view_changed(self) -> None:
        if self.channel_panel.favorites_only:
            favs = [Channel.from_dict(d) for d in self.settings.get_favorites()]
            self.channel_panel.set_channels(favs, country_name="Favoriler")
            self.status.set_text(f"{len(favs)} favori kanal", T.TEXT_ACCENT)
        else:
            if self._current_country:
                self.channel_panel.set_channels(
                    self._current_channels,
                    country_name=self._current_country.name,
                )
                self.status.set_text(
                    f"{self._current_country.name}: {len(self._current_channels)} kanal"
                )

    # -------------------------------------------------------------- close
    def _on_close(self) -> None:
        try:
            # Remember geometry unless maximized
            try:
                maximized = self.state() == "zoomed"
            except Exception:
                maximized = False
            self.settings.window_maximized = maximized
            if not maximized:
                self.settings.geometry = self.geometry()
        except Exception:
            pass
        try:
            self.player.release()
        except Exception:
            pass
        self.destroy()
