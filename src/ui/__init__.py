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
from .visual import build_request_from_form_values, run_visual_app, submit_visual_form_values

__all__ = [
    "DocxReportGenerator",
    "TraceabilityCaseRunner",
    "UiGenerationRequest",
    "UiGenerationResult",
    "build_parser",
    "build_request_from_args",
    "build_request_from_form_values",
    "generate_report_from_ui_request",
    "main",
    "run_visual_app",
    "submit_visual_form_values",
    "validate_ui_generation_request",
]
