"""UI orchestration boundary for TraceAI Control."""

from .cli import build_parser, build_request_from_args, main
from .orchestrator import (
    DocxReportGenerator,
    TraceabilityCaseRunner,
    UiGenerationRequest,
    UiGenerationResult,
    generate_report_from_ui_request,
    validate_ui_generation_request,
)

__all__ = [
    "DocxReportGenerator",
    "TraceabilityCaseRunner",
    "UiGenerationRequest",
    "UiGenerationResult",
    "build_parser",
    "build_request_from_args",
    "generate_report_from_ui_request",
    "main",
    "validate_ui_generation_request",
]
