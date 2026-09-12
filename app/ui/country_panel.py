"""Left sidebar: country search + list."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from app.models import Country
from app.ui import theme as T
from app.ui.widgets import SearchBox


class CountryPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_select: Callable[[Country], None],
        on_refresh: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            width=T.SIDEBAR_WIDTH,
            fg_color=T.BG_SIDEBAR,
            corner_radius=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self._on_select = on_select
        self._on_refresh = on_refresh
        self._countries: list[Country] = []
        self._filtered: list[Country] = []
        self._selected_code: Optional[str] = None
        self._row_widgets: list[ctk.CTkFrame] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="Ülkeler",
            font=T.FONT_HEADING,
            text_color=T.TEXT,
            anchor="w",
        ).pack(side="left")
        self.refresh_btn = ctk.CTkButton(
            header,
            text="↻",
            width=32,
            height=28,
            fg_color=T.BG_CARD,
            hover_color=T.ACCENT,
            text_color=T.TEXT,
            corner_radius=8,
            command=self._refresh_clicked,
        )
        self.refresh_btn.pack(side="right")

        self.search = SearchBox(self, placeholder="Ülke ara…", command=self._apply_filter)
        self.search.pack(fill="x", padx=14, pady=(0, 10))

        self.count_label = ctk.CTkLabel(
            self,
            text="",
            font=T.FONT_SMALL,
            text_color=T.TEXT_DIM,
            anchor="w",
        )
        self.count_label.pack(fill="x", padx=16, pady=(0, 4))

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=T.BORDER,
            scrollbar_button_hover_color=T.ACCENT,
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    def set_countries(self, countries: list[Country], select_code: Optional[str] = None) -> None:
        self._countries = list(countries)
        self._apply_filter(self.search.get())
        if select_code:
            self.select_code(select_code)

    def select_code(self, code: str) -> None:
        code = code.lower()
        self._selected_code = code
        self._render()
        for c in self._countries:
            if c.code == code:
                self._on_select(c)
                break

    def _refresh_clicked(self) -> None:
        if self._on_refresh:
            self._on_refresh()

    def _apply_filter(self, query: str) -> None:
        q = (query or "").strip().casefold()
        if not q:
            self._filtered = list(self._countries)
        else:
            self._filtered = [
                c
                for c in self._countries
                if q in c.name.casefold() or q in c.code.casefold()
            ]
        self.count_label.configure(text=f"{len(self._filtered)} ülke")
        self._render()

    def _render(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()

        for country in self._filtered:
            selected = country.code == self._selected_code
            row = ctk.CTkFrame(
                self.list_frame,
                fg_color=T.ACCENT_SOFT if selected else T.BG_CARD,
                corner_radius=10,
                height=48,
            )
            row.pack(fill="x", pady=3, padx=2)
            row.pack_propagate(False)

            label_text = f"{country.flag}  {country.name}" if country.flag else country.name
            meta = ""
            if country.channel_count:
                meta = f"  ·  {country.channel_count}"

            btn = ctk.CTkButton(
                row,
                text=f"{label_text}{meta}",
                anchor="w",
                fg_color="transparent",
                hover_color=T.BG_CARD_HOVER if not selected else T.ACCENT,
                text_color=T.TEXT_ACCENT if selected else T.TEXT,
                font=T.FONT_BODY,
                height=44,
                command=lambda c=country: self._clicked(c),
            )
            btn.pack(fill="both", expand=True, padx=4, pady=2)
            self._row_widgets.append(row)

    def _clicked(self, country: Country) -> None:
        self._selected_code = country.code
        self._render()
        self._on_select(country)
