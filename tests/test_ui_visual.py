from src.ui.audit_checklist_section_widgets import build_section_display_model
from src.ui.audit_checklist_view_model import AuditChecklistUiSection, AuditChecklistUiViewModel
from src.ui.orchestrator import UiGenerationRequest, UiGenerationResult
from src.ui.visual import (
    VisualAuditChecklistResult,
    build_request_from_form_values,
    format_audit_checklist_preview,
    format_section_display_text,
    submit_audit_checklist_form_values,
    submit_visual_form_values,
    validate_audit_checklist_form_values,
)


def test_build_request_from_form_values_maps_visual_fields() -> None:
    request = build_request_from_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
    )

    assert request == UiGenerationRequest(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
    )


def test_submit_visual_form_values_calls_orchestrator_handler() -> None:
    received_requests: list[UiGenerationRequest] = []

    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        received_requests.append(request)
        return UiGenerationResult(
            success=True,
            output_path="/tmp/report.docx",
            message="Raport generat cu succes: /tmp/report.docx",
        )

    result = submit_visual_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        output_docx_path="/tmp/report.docx",
        request_handler=handler,
    )

    assert result.success is True
    assert result.output_path == "/tmp/report.docx"
    assert received_requests == [
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        )
    ]


def test_submit_visual_form_values_returns_error_from_handler() -> None:
    def handler(request: UiGenerationRequest) -> UiGenerationResult:
        return UiGenerationResult(
            success=False,
            output_path=None,
            message="Eroare la generarea raportului.",
            error="missing code",
        )

    result = submit_visual_form_values(
        source_directory="/data",
        code="",
        lot="L001",
        output_docx_path="/tmp/report.docx",
        request_handler=handler,
    )

    assert result.success is False
    assert result.output_path is None
    assert result.error == "missing code"


def test_validate_audit_checklist_form_values_reports_missing_fields() -> None:
    assert validate_audit_checklist_form_values("/data", "DS0001", "L001") is None
    assert validate_audit_checklist_form_values("", " ", "L001") == "Câmpuri obligatorii lipsă: source_directory, code"


def test_submit_audit_checklist_form_values_builds_view_model_from_payload() -> None:
    payload_calls: list[tuple[str, str, str]] = []
    view_model_calls: list[dict] = []
    expected_view_model = make_visual_view_model()

    def payload_builder(source_directory: str, code: str, lot: str) -> dict:
        payload_calls.append((source_directory, code, lot))
        return {"schema_version": "audit-checklist-ui.v1", "sections": []}

    def view_model_builder(payload: dict) -> AuditChecklistUiViewModel:
        view_model_calls.append(payload)
        return expected_view_model

    result = submit_audit_checklist_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        payload_builder=payload_builder,
        view_model_builder=view_model_builder,
    )

    assert result == VisualAuditChecklistResult(
        success=True,
        view_model=expected_view_model,
        message="Previzualizare audit checklist generată cu succes.",
    )
    assert payload_calls == [("/data", "DS0001", "L001")]
    assert view_model_calls == [{"schema_version": "audit-checklist-ui.v1", "sections": []}]


def test_submit_audit_checklist_form_values_returns_validation_error_without_engine_call() -> None:
    calls: list[str] = []

    def payload_builder(source_directory: str, code: str, lot: str) -> dict:
        calls.append("payload")
        return {}

    result = submit_audit_checklist_form_values(
        source_directory="",
        code="DS0001",
        lot="",
        payload_builder=payload_builder,
    )

    assert result.success is False
    assert result.view_model is None
    assert result.error == "Câmpuri obligatorii lipsă: source_directory, lot"
    assert calls == []


def test_submit_audit_checklist_form_values_returns_builder_error() -> None:
    def failing_payload_builder(source_directory: str, code: str, lot: str) -> dict:
        raise RuntimeError("payload failed")

    result = submit_audit_checklist_form_values(
        source_directory="/data",
        code="DS0001",
        lot="L001",
        payload_builder=failing_payload_builder,
    )

    assert result.success is False
    assert result.view_model is None
    assert result.message == "Eroare la generarea previzualizării audit checklist."
    assert result.error == "payload failed"


def test_format_audit_checklist_preview_renders_subject_details_and_limited_rows() -> None:
    view_model = make_visual_view_model()

    preview = format_audit_checklist_preview(view_model, max_rows_per_section=1)

    assert "Schema: audit-checklist-ui.v1" in preview
    assert "Produs: DS0001 / L001" in preview
    assert "Rezultat: PASS" in preview
    assert "1. Bilanț produs finit" in preview
    assert "- prd_produced: 10 KG" in preview
    assert "2. Livrări" in preview
    assert "Rânduri: 2" in preview
    assert "[1] document=D1; client=C1" in preview
    assert "... încă 1 rând(uri)" in preview


def test_format_section_display_text_renders_selected_details_section() -> None:
    display = build_section_display_model(make_visual_view_model().sections[0])

    text = format_section_display_text(display)

    assert text == (
        "Bilanț produs finit\n"
        "Detalii bilanț.\n"
        "2 câmp(uri)\n"
        "- prd_produced: 10 KG\n"
        "- delivered: 3 KG\n"
    )


def test_format_section_display_text_renders_selected_table_section() -> None:
    display = build_section_display_model(make_visual_view_model().sections[1])

    text = format_section_display_text(display)

    assert text == (
        "Livrări\n"
        "Livrări aval.\n"
        "2 rând(uri)\n"
        "Document | Client\n"
        "D1 | C1\n"
        "D2 | C2\n"
    )


def make_visual_view_model() -> AuditChecklistUiViewModel:
    return AuditChecklistUiViewModel(
        schema_version="audit-checklist-ui.v1",
        subject={
            "code": "DS0001",
            "lot": "L001",
            "product_name": "Produs test",
            "result": "PASS",
        },
        sections=[
            AuditChecklistUiSection(
                key="balance",
                title="Bilanț produs finit",
                description="Detalii bilanț.",
                kind="details",
                data={"prd_produced": "10 KG", "delivered": "3 KG"},
                field_keys=["prd_produced", "delivered"],
            ),
            AuditChecklistUiSection(
                key="downstream",
                title="Livrări",
                description="Livrări aval.",
                kind="table",
                rows=[
                    {"document": "D1", "client": "C1"},
                    {"document": "D2", "client": "C2"},
                ],
                column_keys=["document", "client"],
            ),
        ],
    )
