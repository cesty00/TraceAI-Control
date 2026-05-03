import json
import zipfile
from pathlib import Path

from src.support.diagnostic_bundle import (
    build_diagnostic_bundle,
    default_diagnostic_zip_path,
    sanitize_filename_part,
)


def test_build_diagnostic_bundle_writes_support_zip(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    report_path = tmp_path / "raport.docx"
    report_path.write_bytes(b"demo-docx")
    output_zip = tmp_path / "diagnostic.zip"

    result = build_diagnostic_bundle(tmp_path, "DS0001", "L001", output_zip, report_path)

    assert result == output_zip.resolve()
    assert output_zip.exists()
    with zipfile.ZipFile(output_zip) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "README.txt" in names
        assert "build_info.json" in names
        assert "source_inventory.json" in names
        assert "preflight.json" in names
        assert "audit_checklist_ui.json" in names or "audit_checklist_ui_error.json" in names
        assert "reports/raport.docx" in names
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        preflight = json.loads(archive.read("preflight.json").decode("utf-8"))

    assert manifest["schema_version"] == "traceai-diagnostic-bundle.v1"
    assert manifest["code"] == "DS0001"
    assert manifest["lot"] == "L001"
    assert preflight["schema_version"] == "preflight-report.v1"


def test_default_diagnostic_zip_path_sanitizes_code_and_lot(tmp_path: Path) -> None:
    path = default_diagnostic_zip_path(tmp_path, "DS/001", "LOT 1")

    assert path.parent == tmp_path.resolve()
    assert path.name.startswith("TraceAI-Diagnostic-DS_001-LOT_1-")
    assert path.suffix == ".zip"
    assert sanitize_filename_part(" / ") == "UNKNOWN"


def write_minimal_sources(folder: Path) -> None:
    (folder / "trasabilitate_wms.csv").write_text(
        "cod,lot,cantitate,um,document\nDS0001,L001,10,kg,WMS-1\n",
        encoding="utf-8",
    )
    (folder / "rapoarte productie.csv").write_text(
        "cod,lot,cantitate,um,comanda\nDS0001,L001,10,kg,PRD-1\n",
        encoding="utf-8",
    )
    write_minimal_xlsx(folder / "nomenclator.xlsx", headers=["cod", "lot", "denumire"], row=["DS0001", "L001", "Produs test"])
    write_minimal_xlsx(folder / "stoc la moment original.xlsx", headers=["cod", "lot", "stoc"], row=["DS0001", "L001", "5"])


def write_minimal_xlsx(path: Path, headers: list[str], row: list[str]) -> None:
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
