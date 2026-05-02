"""Report Engine package for TraceAI Control."""

from __future__ import annotations

from typing import Any

__all__ = ["generate_minimal_docx_report"]


def __getattr__(name: str) -> Any:
    """Lazily expose report helpers without importing runnable modules early.

    The diagnostics workflow executes ``python -m src.report.docx_minimal``.
    Importing ``docx_minimal`` from this package initializer before that module
    is executed triggers Python's runpy warning. Lazy export keeps the public
    package API while avoiding eager import side effects.
    """

    if name == "generate_minimal_docx_report":
        from .docx_minimal import generate_minimal_docx_report

        return generate_minimal_docx_report
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
