from concurrent.futures import ThreadPoolExecutor

from src.core.preflight_report import PreflightReport, PreflightSubjectStatus
from src.ui.visual import VisualPreflightResult, submit_preflight_form_values, submit_preflight_form_values_async


def test_submit_preflight_form_values_rejects_missing_fields() -> None:
    result = submit_preflight_form_values("", "DS0001", "L001")

    assert result.success is False
    assert result.report is None
    assert result.error == "Câmpuri obligatorii lipsă: source_directory"


def test_submit_preflight_form_values_async_uses_request_handler() -> None:
    report = PreflightReport(
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
        status="OK",
    )

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
