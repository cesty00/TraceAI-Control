"""UI action helpers for generating TraceAI diagnostic ZIP bundles.

This module keeps diagnostic ZIP generation independent from Tkinter widgets.
The visual UI can call these helpers from a background executor and render the
returned status safely on the UI thread.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Executor, Future
from dataclasses import dataclass
from pathlib import Path

from src.support.diagnostic_bundle import build_diagnostic_bundle, default_diagnostic_zip_path

DiagnosticBundleBuilder = Callable[[str, str, str, str, str | None], Path]


@dataclass(frozen=True)
class VisualDiagnosticBundleResult:
    """Stable status returned when UI requests a diagnostic ZIP."""

    success: bool
    output_zip_path: str | None
    message: str
    error: str | None = None


def validate_diagnostic_bundle_form_values(
    source_directory: str,
    code: str,
    lot: str,
    output_zip_path: str,
) -> str | None:
    """Validate fields needed for diagnostic bundle generation."""

    missing_fields = [
        field_name
        for field_name, field_value in (
            ("source_directory", source_directory),
            ("code", code),
            ("lot", lot),
            ("output_zip_path", output_zip_path),
        )
        if not str(field_value).strip()
    ]
    if missing_fields:
        return "Câmpuri obligatorii lipsă: " + ", ".join(missing_fields)
    return None


def resolve_optional_generated_report_path(generated_report_path: str | None) -> tuple[str | None, str | None]:
    """Return an attachable DOCX path and an optional user-facing note."""

    if not generated_report_path or not str(generated_report_path).strip():
        return None, None
    report_path = Path(generated_report_path).expanduser()
    if report_path.is_file():
        return str(report_path), None
    return None, f"Raport DOCX opțional neatâșat: fișierul nu există la {report_path}."


def submit_diagnostic_bundle_form_values(
    source_directory: str,
    code: str,
    lot: str,
    output_zip_path: str,
    generated_report_path: str | None = None,
    bundle_builder: DiagnosticBundleBuilder | None = None,
) -> VisualDiagnosticBundleResult:
    """Generate diagnostic ZIP from visual form values."""

    validation_error = validate_diagnostic_bundle_form_values(source_directory, code, lot, output_zip_path)
    if validation_error:
        return VisualDiagnosticBundleResult(
            success=False,
            output_zip_path=None,
            message="Date UI incomplete pentru diagnostic ZIP.",
            error=validation_error,
        )

    attachable_report_path, attachment_note = resolve_optional_generated_report_path(generated_report_path)

    try:
        builder = bundle_builder or default_diagnostic_bundle_builder
        output = builder(source_directory, code, lot, output_zip_path, attachable_report_path)
    except Exception as exc:  # pragma: no cover - exact exception belongs to support/core layers
        return VisualDiagnosticBundleResult(
            success=False,
            output_zip_path=None,
            message="Eroare la generarea diagnosticului ZIP.",
            error=str(exc),
        )

    message = f"Diagnostic ZIP generat: {output}"
    if attachment_note:
        message = f"{message}\n{attachment_note}"
    return VisualDiagnosticBundleResult(
        success=True,
        output_zip_path=str(output),
        message=message,
        error=None,
    )


def submit_diagnostic_bundle_form_values_async(
    source_directory: str,
    code: str,
    lot: str,
    output_zip_path: str,
    generated_report_path: str | None,
    executor: Executor,
    request_handler: Callable[[str, str, str, str, str | None], VisualDiagnosticBundleResult] = submit_diagnostic_bundle_form_values,
) -> Future[VisualDiagnosticBundleResult]:
    """Submit diagnostic ZIP generation on a background executor."""

    return executor.submit(
        request_handler,
        source_directory,
        code,
        lot,
        output_zip_path,
        generated_report_path,
    )


def default_diagnostic_bundle_builder(
    source_directory: str,
    code: str,
    lot: str,
    output_zip_path: str,
    generated_report_path: str | None = None,
) -> Path:
    """Adapter around support-layer diagnostic bundle generation."""

    return build_diagnostic_bundle(source_directory, code, lot, output_zip_path, generated_report_path)


def suggest_diagnostic_zip_path(output_directory: str, code: str, lot: str) -> str:
    """Return a default ZIP path suitable for a save dialog initial value."""

    return str(default_diagnostic_zip_path(output_directory, code, lot))
