"""UI orchestration boundary for TraceAI Control."""

from .audit_checklist_contract import UI_SCHEMA_VERSION
from .audit_checklist_view_model import (
    AuditChecklistUiSection,
    AuditChecklistUiViewModel,
    build_audit_checklist_ui_view_model,
    validate_audit_checklist_ui_payload,
)
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
    "AuditChecklistUiSection",
    "AuditChecklistUiViewModel",
    "DocxReportGenerator",
    "TraceabilityCaseRunner",
    "UI_SCHEMA_VERSION",
    "UiGenerationRequest",
    "UiGenerationResult",
    "build_audit_checklist_ui_view_model",
    "build_parser",
    "build_request_from_args",
    "build_request_from_form_values",
    "generate_report_from_ui_request",
    "main",
    "run_visual_app",
    "submit_visual_form_values",
    "validate_audit_checklist_ui_payload",
    "validate_ui_generation_request",
]
