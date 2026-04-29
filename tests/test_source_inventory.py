import csv
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.source_inventory import build_inventory_report, report_to_dict


def write_minimal_xlsx(path: Path, sheet_name: str, headers: list[str]) -> None:
    cells = "".join(
        f'<c r="{chr(65 + index)}1" t="inlineStr"><is><t>{escape(header)}</t></is></c>'
        for index, header in enumerate(headers)
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row r="1">{cells}</row></sheetData>'
        '</worksheet>'
    )

    with zipfile.ZipFile(path, "w") as workbook:
        workbook.writestr("[Content_Types].xml", "")
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>',
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        )
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def test_build_inventory_report_detects_csv_and_xlsx(tmp_path: Path) -> None:
    csv_path = tmp_path / "trasabilitate_wms.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Cod articol", "Lot", "Cantitate"])
        writer.writerow(["DS0001", "L001", "10"])

    product_path = tmp_path / "rapoarte productie.csv"
    with product_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Cod produs", "Lot produs"])
        writer.writerow(["DS0001", "L001"])

    write_minimal_xlsx(tmp_path / "nomenclator.xlsx", "Articole", ["Cod", "Denumire"])
    write_minimal_xlsx(tmp_path / "stoc la moment original.xlsx", "Stoc", ["Cod", "Lot", "Stoc"])

    report = build_inventory_report(tmp_path)
    data = report_to_dict(report)

    assert data["problems"] == []
    assert len(data["sources"]) == 4

    wms = data["sources"][0]
    assert wms["found"] is True
    assert wms["file_type"] == "csv"
    assert wms["row_count"] == 1
    assert wms["columns"] == ["Cod articol", "Lot", "Cantitate"]

    nomenclator = data["sources"][2]
    assert nomenclator["found"] is True
    assert nomenclator["file_type"] == "xlsx"
    assert nomenclator["sheets"][0]["name"] == "Articole"
    assert nomenclator["sheets"][0]["columns"] == ["Cod", "Denumire"]


def test_build_inventory_report_marks_missing_sources(tmp_path: Path) -> None:
    report = build_inventory_report(tmp_path)
    data = report_to_dict(report)

    assert len(data["sources"]) == 4
    assert all(source["found"] is False for source in data["sources"])
    assert len(data["problems"]) == 4
