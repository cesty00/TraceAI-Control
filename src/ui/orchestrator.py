"""UI orchestration boundary for TraceAI Control.

This module is intentionally small. It collects already provided parameters,
invokes the existing engine, and returns a stable status object.

It does not read operational source files directly and does not contain business
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from src.report.docx_minimal import generate_minimal_docx_report
from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import TraceabilityCase


class TraceabilityCaseRunner(Protocol):
    """Callable contract for building a TraceabilityCase."""

    def __call__(self, source_directory: str, code: str, lot: str) -> TraceabilityCase:
        """Build and return a TraceabilityCase."""


class DocxReportGenerator(Protocol):
    """Callable contract for generating the DOCX report."""

    def __call__(self, traceability_case: TraceabilityCase, output_path: str | Path) -> Path:
        """Generate a DOCX report and return its output path."""


@dataclass(frozen=True)
class UiGenerationRequest:
    """Input collected by the future UI layer."""

    source_directory: str
    code: str
    lot: str
    output_docx_path: str


@dataclass(frozen=True)
class UiGenerationResult:
    """Stable status returned to the future UI layer."""

    success: bool
    output_path: str | None
    message: str
    error: str | None = None


def generate_report_from_ui_request(
    request: UiGenerationRequest,
    traceability_case_runner: TraceabilityCaseRunner = run_traceability_case,
    docx_report_generator: DocxReportGenerator = generate_minimal_docx_report,
) -> UiGenerationResult:
    """Generate a report by orchestrating the existing engine.

    The function validates only the minimal UI fields. It delegates all business
    logic to Core/Rules/Report Engine.
    """

    validation_error = validate_ui_generation_request(request)
    if validation_error:
        return UiGenerationResult(
            success=False,
            output_path=None,
            message="Date UI incomplete pentru generarea raportului.",
            error=validation_error,
        )

    try:
        traceability_case = traceability_case_runner(
            request.source_directory,
            request.code,
            request.lot,
        )
        output_path = docx_report_generator(traceability_case, request.output_docx_path)
    except Exception as exc:  # pragma: no cover - exact exception belongs to engine layer
        return UiGenerationResult(
            success=False,
            output_path=None,
            message="Eroare la generarea raportului.",
            error=str(exc),
        )

    return UiGenerationResult(
        success=True,
        output_path=str(output_path),
        message=f"Raport generat cu succes: {output_path}",
        error=None,
    )


def validate_ui_generation_request(request: UiGenerationRequest) -> str | None:
    """Validate only required UI fields, not business data."""

    missing_fields = [
        field_name
        for field_name, field_value in (
            ("source_directory", request.source_directory),
            ("code", request.code),
            ("lot", request.lot),
            ("output_docx_path", request.output_docx_path),
        )
        if not str(field_value).strip()
    ]
    if missing_fields:
        return "Câmpuri obligatorii lipsă: " + ", ".join(missing_fields)
    return None
