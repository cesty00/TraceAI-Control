"""Embedded branding assets for the TraceAI Control visual UI.

The visual shell keeps branding in code so packaged builds do not depend on
ad-hoc external image paths.
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

PhotoImageFactory = Callable[..., Any]

_APP_LOGO_PNG_BASE64 = (
    "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"
)


def app_logo_png_bytes() -> bytes:
    """Return the embedded TraceAI Control logo as PNG bytes."""

    return base64.b64decode(_APP_LOGO_PNG_BASE64)


def create_app_logo_image(photo_image_factory: PhotoImageFactory, master: object | None = None) -> object:
    """Build a Tk-compatible image from the embedded logo payload."""

    return photo_image_factory(master=master, data=_APP_LOGO_PNG_BASE64)


def load_tk_logo_image(master: object | None = None) -> object | None:
    """Load the embedded logo as a Tk PhotoImage when Tkinter is available."""

    try:
        import tkinter as tk
    except Exception:
        return None

    try:
        return create_app_logo_image(tk.PhotoImage, master=master)
    except Exception:
        return None


def apply_app_icon(root: object) -> bool:
    """Apply the embedded logo as the application window icon."""

    image = load_tk_logo_image(master=root)
    if image is None:
        return False

    try:
        root.iconphoto(True, image)
    except Exception:
        return False

    setattr(root, "_traceai_app_icon", image)
    return True