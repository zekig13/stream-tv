"""Application entry — configure DPI-friendly CustomTkinter and launch."""

from __future__ import annotations

import sys


def main() -> int:
    # Windows: improve scaling on HiDPI displays
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
        except Exception:
            try:
                import ctypes

                ctypes.windll.user32.SetProcessDPIAware()  # type: ignore[attr-defined]
            except Exception:
                pass

    from app.ui.main_window import StreamTVApp

    app = StreamTVApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
