from pathlib import Path

from src.core.build_info import BuildInfo
from src.core.preflight_report import (
    STATUS_BLOCKER,
    STATUS_OK,
    build_preflight_report,
    format_preflight_report,
    preflight_report_to_dict,
)


def test_build_preflight_report_ok_for_minimal_sources(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    build_info = BuildInfo(
        app_name="TraceAI Control",
        app_version="1.0.0",
        build_commit="abcdef1234567890",
        build_date="build-date",
        build_channel="test",
        generated_at="generated-at",
    )

    report = build_preflight_report(tmp_path, "DS0001", "L001", build_info=build_info)
    data = preflight_report_to_dict(report)
    text = format_preflight_report(report)

    assert report.status == STATUS_OK
    assert report.subject.total_records == 4
    assert report.subject.records_by_source == {"nomenclator": 1, "production": 1, "stock": 1, "wms": 1}
    assert all(source.status == STATUS_OK for source in report.sources)
    assert data["schema_version"] == "preflight-report.v1"
    assert data["build_info"]["build_commit"] == "abcdef1234567890"
    assert "WMS trasabilitate: OK" in text
    assert "Raport producție PRD: OK" in text
    assert "Cod+lot pe surse:" in text


def test_build_preflight_report_warns_when_subject_is_absent_from_stock(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path, stock_code="OTHER", stock_lot="OTHER")

    report = build_preflight_report(tmp_path, "DS0001", "L001")

    assert report.status == "WARNING"
    assert report.subject.records_by_source == {"nomenclator": 1, "production": 1, "wms": 1}
    assert any("poate fi normal dacă nu există stoc fizic" in warning for warning in report.warnings)
    assert not report.blockers


def test_build_preflight_report_blocks_when_required_sources_missing(tmp_path: Path) -> None:
    (tmp_path / "trasabilitate_wms.csv").write_text("cod,lot,cantitate\nDS0001,L001,10\n", encoding="utf-8")

    report = build_preflight_report(tmp_path, "DS0001", "L001")

    assert report.status == STATUS_BLOCKER
    assert any("Raport producție PRD" in blocker for blocker in report.blockers)
    assert any("Nomenclator" in blocker for blocker in report.blockers)
    assert any("Stoc la moment" in blocker for blocker in report.blockers)
    assert report.subject.total_records == 1


def test_build_preflight_report_blocks_when_code_lot_not_found(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)

    report = build_preflight_report(tmp_path, "DS404", "LOT404")

    assert report.status == STATUS_BLOCKER
    assert report.subject.total_records == 0
    assert "Codul și lotul nu au fost găsite în sursele normalizate." in report.blockers


def write_minimal_sources(folder: Path, stock_code: str = "DS0001", stock_lot: str = "L001") -> None:
    (folder / "trasabilitate_wms.csv").write_text(
        "cod,lot,cantitate,um,document\nDS0001,L001,10,kg,WMS-1\n",
        encoding="utf-8",
    )
    (folder / "rapoarte productie.csv").write_text(
        "cod,lot,cantitate,um,comanda\nDS0001,L001,10,kg,PRD-1\n",
        encoding="utf-8",
    )
    write_minimal_xlsx(folder / "nomenclator.xlsx", headers=["cod", "lot", "denumire"], row=["DS0001", "L001", "Produs test"])
    write_minimal_xlsx(folder / "stoc la moment original.xlsx", headers=["cod", "lot", "stoc"], row=[stock_code, stock_lot, "5"])


def write_minimal_xlsx(path: Path, headers: list[str], row: list[str]) -> None:
    import zipfile

    def cell(column: str, row_number: int, value: str) -> str:
        return f'<c r="{column}{row_number}" t="inlineStr"><is><t>{value}</t></is></c>'

    header_xml = "".join(cell(chr(ord("A") + index), 1, value) for index, value in enumerate(headers))
    row_xml = "".join(cell(chr(ord("A") + index), 2, value) for index, value in enumerate(row))
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row r="1">{header_xml}</row><row r="2">{row_xml}</row></sheetData>'
        '</worksheet>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("xl/workbook.xml", workbook_xml)
        package.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        package.writestr("xl/worksheets/sheet1.xml", sheet_xml)
