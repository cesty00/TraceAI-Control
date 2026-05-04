"""Branded entry point for the TraceAI Control visual app."""

from __future__ import annotations

import importlib
import sys

from src.ui.branding import apply_app_icon



def run_branded_visual_app() -> int:
    """Run the visual UI while applying the embedded window icon."""

    import tkinter as tk

    visual = sys.modules.get("src.ui.visual")
    if visual is None:
        visual = importlib.import_module("src.ui.visual")
    original_tk = tk.Tk

    def create_root(*args: object, **kwargs: object) -> object:
        root = original_tk(*args, **kwargs)
        apply_app_icon(root)
        return root

    tk.Tk = create_root  # type: ignore[assignment]
    try:
        return visual.main()
    finally:
        tk.Tk = original_tk  # type: ignore[assignment]



def main() -> int:
    """Command-line entry point for the branded visual app."""

    return run_branded_visual_app()


if __name__ == "__main__":
    raise SystemExit(main())
