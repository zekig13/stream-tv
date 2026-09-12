"""Download and cache channel logos for CustomTkinter / CTkImage."""

from __future__ import annotations

import hashlib
import io
import threading
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageDraw

from app.fetcher.client import polite_get
from app.settings.config import LOGO_CACHE_DIR
from app.ui.theme import ACCENT, BG_CARD, LOGO_SIZE

_placeholder: Optional[Image.Image] = None
_lock = threading.Lock()


def _make_placeholder(size: int = LOGO_SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG_CARD)
    draw = ImageDraw.Draw(img)
    margin = size // 6
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 5,
        fill=ACCENT,
    )
    # simple play triangle
    cx, cy = size // 2, size // 2
    draw.polygon(
        [(cx - size // 8, cy - size // 6), (cx - size // 8, cy + size // 6), (cx + size // 5, cy)],
        fill="white",
    )
    return img


def placeholder_image(size: int = LOGO_SIZE) -> Image.Image:
    global _placeholder
    with _lock:
        if _placeholder is None or _placeholder.size[0] != size:
            _placeholder = _make_placeholder(size)
        return _placeholder.copy()


def _cache_path(url: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return LOGO_CACHE_DIR / f"{digest}.png"


def load_logo(
    url: str,
    size: int = LOGO_SIZE,
    on_done: Optional[Callable[[Image.Image], None]] = None,
) -> Image.Image:
    """
    Return a placeholder immediately; if url is set, fetch in background
    and call on_done(pil_image) on success.
    """
    ph = placeholder_image(size)
    if not url:
        return ph

    path = _cache_path(url)
    if path.exists():
        try:
            img = Image.open(path).convert("RGBA")
            img = _fit(img, size)
            if on_done:
                on_done(img)
            return img
        except OSError:
            pass

    def worker() -> None:
        try:
            LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            resp = polite_get(url, timeout=12)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            img = _fit(img, size)
            img.save(path, format="PNG")
            if on_done:
                on_done(img)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()
    return ph


def _fit(img: Image.Image, size: int) -> Image.Image:
    img = img.copy()
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y), img if img.mode == "RGBA" else None)
    return canvas
