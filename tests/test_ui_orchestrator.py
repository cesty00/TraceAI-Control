from dataclasses import replace
from pathlib import Path

from src.errors import MissingSourceFileError
from src.rules.traceability_case import TraceabilityCase, TraceabilityCaseSubject
from src.ui.orchestrator import (
    UiGenerationRequest,
    generate_audit_checklist_docx_from_traceability_case,
    generate_report_from_ui_request,
    validate_ui_generation_request,
)
from tests.test_audit_traceability_report import make_case


def test_generate_report_from_ui_request_orchestrates_existing_engine() -> None:
    calls: list[tuple[str, object]] = []
    expected_output = str(Path("/tmp/report.docx"))

    def fake_runner(source_directory: str, code: str, lot: str) -> TraceabilityCase:
        calls.append(("runner", (source_directory, code, lot)))
        return TraceabilityCase(subject=TraceabilityCaseSubject(code=code, lot=lot, case_type="FINISHED_PRODUCT"))

    def fake_generator(traceability_case: TraceabilityCase, output_path: str | Path) -> Path:
        calls.append(("generator", (traceability_case.subject.code, traceability_case.subject.lot, str(output_path))))
        return Path(output_path)

    result = generate_report_from_ui_request(
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        ),
        traceability_case_runner=fake_runner,
        docx_report_generator=fake_generator,
    )

    assert result.success is True
    assert result.output_path == expected_output
    assert result.error is None
    assert "Raport audit checklist generat cu succes" in result.message
    assert calls == [
        ("runner", ("/data", "DS0001", "L001")),
        ("generator", ("DS0001", "L001", "/tmp/report.docx")),
    ]


def test_generate_audit_checklist_docx_from_traceability_case_is_exported_adapter() -> None:
    assert callable(generate_audit_checklist_docx_from_traceability_case)


def test_generate_audit_checklist_docx_from_traceability_case_wires_data_quality_summary(monkeypatch, tmp_path: Path) -> None:
    traceability_case = make_case()
    data_quality = {
        "status": "WARNING",
        "source_count": 4,
        "sources_found": 4,
        "error_count": 0,
        "warning_count": 8,
        "issue_count": 8,
        "issues": [
            {
                "severity": "WARNING",
                "source_name": "nomenclator.xlsx",
                "sheet_name": "Sheet2",
                "column_name": "cod articol/produs",
                "message": "Observație existentă pentru cazul local/operator.",
            }
        ],
    }
    traceability_case = replace(
        traceability_case,
        sections={**traceability_case.sections, "data_quality": data_quality},
        observations=["Observații Data Quality existente pentru cazul local/operator."],
    )
    captured: dict[str, object] = {}

    def fake_generate(report, output_path, policy=None, build_info=None, data_quality_summary=None):
        captured["output_path"] = Path(output_path)
        captured["data_quality_summary"] = data_quality_summary
        return Path(output_path)

    monkeypatch.setattr("src.ui.orchestrator.generate_audit_checklist_docx_report", fake_generate)

    output = tmp_path / "report.docx"
    result = generate_audit_checklist_docx_from_traceability_case(traceability_case, output)

    assert result == output
    assert captured["output_path"] == output
    assert captured["data_quality_summary"] == data_quality


def test_generate_report_from_ui_request_returns_validation_error_without_engine_call() -> None:
    calls: list[str] = []

    def fake_runner(source_directory: str, code: str, lot: str) -> TraceabilityCase:
        calls.append("runner")
        return TraceabilityCase(subject=TraceabilityCaseSubject(code=code, lot=lot, case_type="UNKNOWN"))

    def fake_generator(traceability_case: TraceabilityCase, output_path: str | Path) -> Path:
        calls.append("generator")
        return Path(output_path)

    result = generate_report_from_ui_request(
        UiGenerationRequest(
            source_directory="/data",
            code="",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        ),
        traceability_case_runner=fake_runner,
        docx_report_generator=fake_generator,
    )

    assert result.success is False
    assert result.output_path is None
    assert result.error == "Câmpuri obligatorii lipsă: code"
    assert calls == []


def test_generate_report_from_ui_request_returns_typed_traceai_error() -> None:
    def failing_runner(source_directory: str, code: str, lot: str) -> TraceabilityCase:
        raise MissingSourceFileError(
            user_message="Nu pot genera raportul: lipsește o sursă obligatorie.",
            technical_detail="Fișier lipsă: trasabilitate_wms.csv",
            recommended_action="Exportă WMS cu layout-ul standard și reîncearcă.",
        )

    result = generate_report_from_ui_request(
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        ),
        traceability_case_runner=failing_runner,
    )

    assert result.success is False
    assert result.output_path is None
    assert result.message == "Nu pot genera raportul: lipsește o sursă obligatorie."
    assert result.error is not None
    assert "Fișier lipsă: trasabilitate_wms.csv" in result.error
    assert "Acțiune recomandată: Exportă WMS cu layout-ul standard și reîncearcă." in result.error


def test_generate_report_from_ui_request_returns_engine_error() -> None:
    def failing_runner(source_directory: str, code: str, lot: str) -> TraceabilityCase:
        raise RuntimeError("engine failed")

    result = generate_report_from_ui_request(
        UiGenerationRequest(
            source_directory="/data",
            code="DS0001",
            lot="L001",
            output_docx_path="/tmp/report.docx",
        ),
        traceability_case_runner=failing_runner,
    )

    assert result.success is False
    assert result.output_path is None
    assert result.message == "Eroare la generarea raportului."
    assert result.error == "engine failed"


def test_validate_ui_generation_request_reports_all_missing_fields() -> None:
    error = validate_ui_generation_request(
        UiGenerationRequest(
            source_directory=" ",
            code="",
            lot="L001",
            output_docx_path="",
        )
    )

    assert error == "Câmpuri obligatorii lipsă: source_directory, code, output_docx_path"
