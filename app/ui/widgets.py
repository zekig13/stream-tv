"""Reusable dark UI widgets."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image

from app.ui import theme as T


class SearchBox(ctk.CTkFrame):
    def __init__(
        self,
        master,
        placeholder: str = "Ara…",
        command: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_INPUT, corner_radius=10, **kwargs)
        self._command = command
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            border_width=0,
            fg_color="transparent",
            text_color=T.TEXT,
            placeholder_text_color=T.TEXT_DIM,
            font=T.FONT_BODY,
            height=36,
        )
        self.entry.pack(fill="x", padx=10, pady=4)
        self.entry.bind("<KeyRelease>", self._on_key)

    def _on_key(self, _event=None) -> None:
        if self._command:
            self._command(self.entry.get())

    def get(self) -> str:
        return self.entry.get()

    def clear(self) -> None:
        self.entry.delete(0, "end")
        if self._command:
            self._command("")


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=T.BG_SIDEBAR, height=32, corner_radius=0, **kwargs)
        self.label = ctk.CTkLabel(
            self,
            text="Hazır",
            font=T.FONT_SMALL,
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.label.pack(side="left", padx=14, pady=4, fill="x", expand=True)

    def set_text(self, text: str, color: str = T.TEXT_MUTED) -> None:
        self.label.configure(text=text, text_color=color)


class EmptyState(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(
            self,
            text=title,
            font=T.FONT_HEADING,
            text_color=T.TEXT_MUTED,
        ).pack(pady=(40, 6))
        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=T.FONT_BODY,
                text_color=T.TEXT_DIM,
                wraplength=420,
                justify="center",
            ).pack()


def pil_to_ctk(img: Image.Image, size: tuple[int, int] | None = None) -> ctk.CTkImage:
    if size is None:
        size = img.size
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)
