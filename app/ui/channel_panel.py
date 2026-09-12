"""Channel list with logos, search, category filter, favorites."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image

from app.models import Channel
from app.settings.config import get_settings
from app.ui import theme as T
from app.ui.logo_cache import load_logo, placeholder_image
from app.ui.widgets import EmptyState, SearchBox, pil_to_ctk


CATEGORY_TR = {
    "news": "Haber",
    "sports": "Spor",
    "general": "Genel",
    "entertainment": "Eğlence",
    "kids": "Çocuk",
    "music": "Müzik",
    "movies": "Film",
    "series": "Dizi",
    "documentary": "Belgesel",
    "religious": "Dini",
    "lifestyle": "Yaşam",
    "business": "İş",
    "education": "Eğitim",
    "culture": "Kültür",
    "cooking": "Yemek",
    "animation": "Animasyon",
    "weather": "Hava",
    "shop": "Alışveriş",
    "legislative": "Meclis",
    "undefined": "Diğer",
}


def category_label(raw: str) -> str:
    if not raw or raw == "Diğer":
        return "Diğer"
    parts = [p.strip() for p in raw.replace("|", ";").split(";") if p.strip()]
    mapped = [CATEGORY_TR.get(p.casefold(), p.title()) for p in parts]
    return " / ".join(mapped)



class ChannelPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_play: Callable[[Channel], None],
        on_favorite_changed: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_ROOT, corner_radius=0, **kwargs)
        self._on_play = on_play
        self._on_favorite_changed = on_favorite_changed
        self._channels: list[Channel] = []
        self._filtered: list[Channel] = []
        self._show_favorites_only = False
        self._category = "Tümü"
        self._row_widgets: list[ctk.CTkBaseClass] = []
        self._logo_images: dict[str, ctk.CTkImage] = {}
        self._country_title = "Kanal Listesi"

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=18, pady=(16, 8))

        self.title_label = ctk.CTkLabel(
            toolbar,
            text=self._country_title,
            font=T.FONT_TITLE,
            text_color=T.TEXT,
            anchor="w",
        )
        self.title_label.pack(side="left")

        self.meta_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=T.FONT_SMALL,
            text_color=T.TEXT_DIM,
            anchor="e",
        )
        self.meta_label.pack(side="right")

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=18, pady=(0, 10))

        self.search = SearchBox(filters, placeholder="Kanal ara…", command=self._apply_filters)
        self.search.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.category_menu = ctk.CTkOptionMenu(
            filters,
            values=["Tümü"],
            width=160,
            height=36,
            fg_color=T.BG_CARD,
            button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER,
            dropdown_fg_color=T.BG_ELEVATED,
            dropdown_hover_color=T.BG_CARD_HOVER,
            text_color=T.TEXT,
            font=T.FONT_BODY,
            command=self._on_category,
        )
        self.category_menu.pack(side="left", padx=(0, 8))

        self.fav_btn = ctk.CTkButton(
            filters,
            text="★ Favoriler",
            width=120,
            height=36,
            fg_color=T.BG_CARD,
            hover_color=T.ACCENT,
            text_color=T.TEXT,
            font=T.FONT_BODY,
            corner_radius=10,
            command=self._toggle_fav_filter,
        )
        self.fav_btn.pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=T.BORDER,
            scrollbar_button_hover_color=T.ACCENT,
        )
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._empty: Optional[EmptyState] = None

    def set_title(self, title: str) -> None:
        self._country_title = title
        self.title_label.configure(text=title)

    def set_channels(self, channels: list[Channel], country_name: str = "") -> None:
        self._channels = list(channels)
        if country_name:
            self.set_title(f"{country_name}")
        cats = sorted({category_label(c.category) for c in self._channels}, key=str.casefold)
        values = ["Tümü"] + cats
        self.category_menu.configure(values=values)
        if self._category not in values:
            self._category = "Tümü"
        self.category_menu.set(self._category)
        self._apply_filters(self.search.get())

    def show_favorites(self, channels: list[Channel]) -> None:
        self._show_favorites_only = True
        self.fav_btn.configure(fg_color=T.ACCENT, text="★ Favoriler ✓")
        self.set_channels(channels, country_name="Favoriler")

    def _toggle_fav_filter(self) -> None:
        self._show_favorites_only = not self._show_favorites_only
        if self._show_favorites_only:
            self.fav_btn.configure(fg_color=T.ACCENT, text="★ Favoriler ✓")
        else:
            self.fav_btn.configure(fg_color=T.BG_CARD, text="★ Favoriler")
        if self._on_favorite_changed:
            # Parent may swap channel source when toggling favorites view
            self._on_favorite_changed()
        self._apply_filters(self.search.get())

    @property
    def favorites_only(self) -> bool:
        return self._show_favorites_only

    def set_favorites_only(self, enabled: bool) -> None:
        self._show_favorites_only = bool(enabled)
        if self._show_favorites_only:
            self.fav_btn.configure(fg_color=T.ACCENT, text="★ Favoriler ✓")
        else:
            self.fav_btn.configure(fg_color=T.BG_CARD, text="★ Favoriler")

    def _on_category(self, value: str) -> None:
        self._category = value
        self._apply_filters(self.search.get())

    def _apply_filters(self, query: str = "") -> None:
        q = (query or self.search.get() or "").strip().casefold()
        settings = get_settings()
        result: list[Channel] = []
        for ch in self._channels:
            if self._show_favorites_only and not settings.is_favorite(ch.favorite_key):
                continue
            if self._category != "Tümü" and category_label(ch.category) != self._category:
                continue
            if q:
                hay = f"{ch.display_name} {ch.category} {ch.tvg_id}".casefold()
                if q not in hay:
                    continue
            result.append(ch)
        self._filtered = result
        self.meta_label.configure(text=f"{len(self._filtered)} / {len(self._channels)} kanal")
        self._render()

    def refresh_favorite_stars(self) -> None:
        self._apply_filters(self.search.get())

    def _clear_rows(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()
        if self._empty is not None:
            self._empty.destroy()
            self._empty = None

    def _render(self) -> None:
        self._clear_rows()
        if not self._filtered:
            self._empty = EmptyState(
                self.list_frame,
                title="Kanal bulunamadı",
                subtitle="Aramayı temizleyin, kategori filtresini değiştirin veya başka bir ülke seçin.",
            )
            self._empty.pack(fill="x", pady=20)
            self._row_widgets.append(self._empty)
            return

        settings = get_settings()
        # Cap initial paint for snappy UI; remaining load on scroll is fine for typical lists
        for ch in self._filtered:
            self._row_widgets.append(self._make_row(ch, settings.is_favorite(ch.favorite_key)))

    def _make_row(self, channel: Channel, is_fav: bool) -> ctk.CTkFrame:
        row = ctk.CTkFrame(
            self.list_frame,
            fg_color=T.BG_CARD,
            corner_radius=12,
            height=T.ROW_HEIGHT + 8,
        )
        row.pack(fill="x", pady=4, padx=4)
        row.pack_propagate(False)

        # Logo
        logo_label = ctk.CTkLabel(row, text="", width=T.LOGO_SIZE + 8, height=T.LOGO_SIZE + 8)
        logo_label.pack(side="left", padx=(10, 6), pady=8)
        ph = placeholder_image(T.LOGO_SIZE)
        ctk_img = pil_to_ctk(ph, (T.LOGO_SIZE, T.LOGO_SIZE))
        self._logo_images[channel.favorite_key] = ctk_img
        logo_label.configure(image=ctk_img)

        def on_logo(img: Image.Image, key=channel.favorite_key, lbl=logo_label) -> None:
            def apply() -> None:
                try:
                    new_img = pil_to_ctk(img, (T.LOGO_SIZE, T.LOGO_SIZE))
                    self._logo_images[key] = new_img
                    lbl.configure(image=new_img)
                except Exception:
                    pass

            try:
                lbl.after(0, apply)
            except Exception:
                pass

        if channel.tvg_logo:
            load_logo(channel.tvg_logo, T.LOGO_SIZE, on_done=on_logo)

        # Text block
        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="both", expand=True, pady=8)

        name_lbl = ctk.CTkLabel(
            text_col,
            text=channel.display_name,
            font=T.FONT_CHANNEL,
            text_color=T.TEXT,
            anchor="w",
        )
        name_lbl.pack(fill="x")
        cat_lbl = ctk.CTkLabel(
            text_col,
            text=category_label(channel.category),
            font=T.FONT_SMALL,
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        cat_lbl.pack(fill="x")

        # Actions
        play_btn = ctk.CTkButton(
            row,
            text="▶ Oynat",
            width=90,
            height=34,
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color="white",
            font=T.FONT_BODY,
            corner_radius=8,
            command=lambda c=channel: self._on_play(c),
        )
        play_btn.pack(side="right", padx=(4, 12))

        star = "★" if is_fav else "☆"
        fav_btn = ctk.CTkButton(
            row,
            text=star,
            width=40,
            height=34,
            fg_color=T.BG_ELEVATED,
            hover_color=T.FAVORITE,
            text_color=T.FAVORITE if is_fav else T.TEXT_MUTED,
            font=(T.FONT_FAMILY, 16),
            corner_radius=8,
            command=lambda c=channel: self._toggle_fav(c),
        )
        fav_btn.pack(side="right", padx=4)

        # Double-click / click name to play
        for w in (row, name_lbl, cat_lbl, logo_label, text_col):
            w.bind("<Double-Button-1>", lambda _e, c=channel: self._on_play(c))

        return row

    def _toggle_fav(self, channel: Channel) -> None:
        settings = get_settings()
        settings.toggle_favorite(channel.to_dict())
        self.refresh_favorite_stars()
        if self._on_favorite_changed:
            self._on_favorite_changed()
