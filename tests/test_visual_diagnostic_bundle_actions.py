from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.ui.diagnostic_bundle_actions import (
    VisualDiagnosticBundleResult,
    resolve_optional_generated_report_path,
    submit_diagnostic_bundle_form_values,
    submit_diagnostic_bundle_form_values_async,
    suggest_diagnostic_zip_path,
    validate_diagnostic_bundle_form_values,
)


def test_validate_diagnostic_bundle_form_values_reports_missing_fields() -> None:
    assert validate_diagnostic_bundle_form_values("", "DS0001", "L001", "out.zip") == "Câmpuri obligatorii lipsă: source_directory"
    assert validate_diagnostic_bundle_form_values("sources", "", "", "") == "Câmpuri obligatorii lipsă: code, lot, output_zip_path"


def test_resolve_optional_generated_report_path_accepts_existing_file(tmp_path: Path) -> None:
    report_path = tmp_path / "raport.docx"
    report_path.write_bytes(b"docx")

    attachable_path, note = resolve_optional_generated_report_path(str(report_path))

    assert attachable_path == str(report_path)
    assert note is None


def test_resolve_optional_generated_report_path_reports_missing_file(tmp_path: Path) -> None:
    missing_report = tmp_path / "missing.docx"

    attachable_path, note = resolve_optional_generated_report_path(str(missing_report))

    assert attachable_path is None
    assert note == f"Raport DOCX opțional neatâșat: fișierul nu există la {missing_report}."


def test_submit_diagnostic_bundle_form_values_uses_builder(tmp_path: Path) -> None:
    output_zip = tmp_path / "diagnostic.zip"
    report_path = tmp_path / "report.docx"
    report_path.write_bytes(b"docx")

    def builder(source_directory: str, code: str, lot: str, output_zip_path: str, generated_report_path: str | None) -> Path:
        assert source_directory == "sources"
        assert code == "DS0001"
        assert lot == "L001"
        assert output_zip_path == str(output_zip)
        assert generated_report_path == str(report_path)
        output_zip.write_bytes(b"zip")
        return output_zip

    result = submit_diagnostic_bundle_form_values("sources", "DS0001", "L001", str(output_zip), str(report_path), builder)

    assert result.success is True
    assert result.output_zip_path == str(output_zip)
    assert "Diagnostic ZIP generat" in result.message


def test_submit_diagnostic_bundle_form_values_skips_missing_optional_report(tmp_path: Path) -> None:
    output_zip = tmp_path / "diagnostic.zip"
    missing_report = tmp_path / "missing.docx"

    def builder(source_directory: str, code: str, lot: str, output_zip_path: str, generated_report_path: str | None) -> Path:
        assert generated_report_path is None
        output_zip.write_bytes(b"zip")
        return output_zip

    result = submit_diagnostic_bundle_form_values("sources", "DS0001", "L001", str(output_zip), str(missing_report), builder)

    assert result.success is True
    assert "Diagnostic ZIP generat" in result.message
    assert f"Raport DOCX opțional neatâșat: fișierul nu există la {missing_report}." in result.message


def test_submit_diagnostic_bundle_form_values_async_uses_request_handler(tmp_path: Path) -> None:
    output_zip = tmp_path / "diagnostic.zip"

    def handler(source_directory: str, code: str, lot: str, output_zip_path: str, generated_report_path: str | None) -> VisualDiagnosticBundleResult:
        assert source_directory == "sources"
        assert code == "DS0001"
        assert lot == "L001"
        assert output_zip_path == str(output_zip)
        assert generated_report_path is None
        return VisualDiagnosticBundleResult(True, str(output_zip), "ok")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = submit_diagnostic_bundle_form_values_async("sources", "DS0001", "L001", str(output_zip), None, executor, handler)
        result = future.result(timeout=2)

    assert result.success is True
    assert result.message == "ok"


def test_suggest_diagnostic_zip_path(tmp_path: Path) -> None:
    suggested = suggest_diagnostic_zip_path(str(tmp_path), "DS/001", "LOT 1")

    assert suggested.startswith(str(tmp_path.resolve()))
    assert "DS_001-LOT_1" in suggested
    assert suggested.endswith(".zip")
