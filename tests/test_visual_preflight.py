from concurrent.futures import ThreadPoolExecutor

from src.core.preflight_report import PreflightReport, PreflightSourceStatus, PreflightSubjectStatus
from src.ui.visual import (
    DOCX_GATE_ALLOW,
    DOCX_GATE_BLOCK,
    DOCX_GATE_CONFIRM,
    PREFLIGHT_BLOCKER_MESSAGE,
    PREFLIGHT_REQUIRED_MESSAGE,
    PREFLIGHT_WARNING_CONFIRMATION_MESSAGE,
    VisualPreflightResult,
    build_preflight_gate_snapshot,
    evaluate_docx_generation_gate,
    submit_preflight_form_values,
    submit_preflight_form_values_async,
)


def test_submit_preflight_form_values_rejects_missing_fields() -> None:
    result = submit_preflight_form_values("", "DS0001", "L001")

    assert result.success is False
    assert result.report is None
    assert result.error == "Câmpuri obligatorii lipsă: source_directory"


def test_submit_preflight_form_values_uses_core_operator_guidance(monkeypatch) -> None:
    report = PreflightReport(
        schema_version="preflight-report.v1",
        source_directory="/tmp/sources",
        build_info={},
        sources=[
            PreflightSourceStatus(
                source_key="wms",
                expected_name="trasabilitate_wms.csv",
                display_name="WMS trasabilitate",
                status="WARNING",
                found=True,
                operator_status="invalid",
                path="/tmp/trasabilitate_wms.csv",
                file_type="csv",
            )
        ],
        subject=PreflightSubjectStatus(
            code="DS0001",
            lot="L001",
            status="OK",
            total_records=2,
            records_by_source={"production": 1, "wms": 1},
        ),
        status="WARNING",
        operator_guidance="Există observații la surse. Poți continua cu atenție.",
    )

    monkeypatch.setattr("src.ui.visual.build_preflight_report", lambda *_args: report)

    result = submit_preflight_form_values("/tmp/sources", "DS0001", "L001")

    assert result.success is True
    assert result.report is report
    assert result.message == "Există observații la surse. Poți continua cu atenție."


def test_submit_preflight_form_values_async_uses_request_handler() -> None:
    report = make_report(status="OK")

    def handler(source_directory: str, code: str, lot: str) -> VisualPreflightResult:
        assert source_directory == "/tmp/sources"
        assert code == "DS0001"
        assert lot == "L001"
        return VisualPreflightResult(success=True, report=report, message="ok")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = submit_preflight_form_values_async("/tmp/sources", "DS0001", "L001", executor, handler)
        result = future.result(timeout=2)

    assert result.success is True
    assert result.report is report
    assert result.message == "ok"


def test_evaluate_docx_generation_gate_blocks_without_current_preflight() -> None:
    decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", None)

    assert decision.status == DOCX_GATE_BLOCK
    assert decision.message == PREFLIGHT_REQUIRED_MESSAGE


def test_evaluate_docx_generation_gate_blocks_when_preflight_has_blockers() -> None:
    snapshot = build_preflight_gate_snapshot("/tmp/sources", "DS0001", "L001", make_report(status="BLOCKER"))

    decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", snapshot)

    assert decision.status == DOCX_GATE_BLOCK
    assert decision.message == PREFLIGHT_BLOCKER_MESSAGE


def test_evaluate_docx_generation_gate_requires_confirmation_on_warning() -> None:
    snapshot = build_preflight_gate_snapshot("/tmp/sources", "DS0001", "L001", make_report(status="WARNING"))

    decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", snapshot)

    assert decision.status == DOCX_GATE_CONFIRM
    assert decision.message == PREFLIGHT_WARNING_CONFIRMATION_MESSAGE


def test_evaluate_docx_generation_gate_allows_generation_on_ok() -> None:
    snapshot = build_preflight_gate_snapshot("/tmp/sources", "DS0001", "L001", make_report(status="OK"))

    decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L001", snapshot)

    assert decision.status == DOCX_GATE_ALLOW
    assert decision.message == "Sursele sunt pregătite. Poți continua cu generarea raportului."


def test_evaluate_docx_generation_gate_invalidates_changed_form_values() -> None:
    snapshot = build_preflight_gate_snapshot("/tmp/sources", "DS0001", "L001", make_report(status="OK"))

    changed_source_decision = evaluate_docx_generation_gate("/tmp/alt-sources", "DS0001", "L001", snapshot)
    changed_code_decision = evaluate_docx_generation_gate("/tmp/sources", "DS0002", "L001", snapshot)
    changed_lot_decision = evaluate_docx_generation_gate("/tmp/sources", "DS0001", "L002", snapshot)

    assert changed_source_decision.status == DOCX_GATE_BLOCK
    assert changed_source_decision.message == PREFLIGHT_REQUIRED_MESSAGE
    assert changed_code_decision.status == DOCX_GATE_BLOCK
    assert changed_code_decision.message == PREFLIGHT_REQUIRED_MESSAGE
    assert changed_lot_decision.status == DOCX_GATE_BLOCK
    assert changed_lot_decision.message == PREFLIGHT_REQUIRED_MESSAGE


def make_report(status: str) -> PreflightReport:
    warnings = ["warning"] if status == "WARNING" else []
    blockers = ["blocker"] if status == "BLOCKER" else []
    guidance = {
        "OK": "Sursele sunt pregătite. Poți continua cu generarea raportului.",
        "WARNING": "Există observații la surse. Poți continua cu atenție.",
        "BLOCKER": "Există blocaje la surse. Oprește-te înainte de generare.",
    }[status]
    return PreflightReport(
        schema_version="preflight-report.v1",
        source_directory="/tmp/sources",
        build_info={},
        sources=[],
        subject=PreflightSubjectStatus(
            code="DS0001",
            lot="L001",
            status="OK",
            total_records=2,
            records_by_source={"production": 1, "wms": 1},
        ),
        status=status,
        operator_guidance=guidance,
        warnings=warnings,
        blockers=blockers,
    )
