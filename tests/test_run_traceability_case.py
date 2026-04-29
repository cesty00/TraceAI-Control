import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from src.rules.case_type_detection import CASE_FINISHED_PRODUCT
from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import traceability_case_to_dict


def write_csv(path: Path, headers: list[str], row: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerow(row)


def write_minimal_xlsx(path: Path, sheet_name: str, headers: list[str], row: list[str]) -> None:
    header_cells = "".join(
        f'<c r="{chr(65 + index)}1" t="inlineStr"><is><t>{escape(header)}</t></is></c>'
        for index, header in enumerate(headers)
    )
    row_cells = "".join(
        f'<c r="{chr(65 + index)}2" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
        for index, value in enumerate(row)
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row r="1">{header_cells}</row><row r="2">{row_cells}</row></sheetData>'
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


def test_run_traceability_case_returns_minimal_case(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "trasabilitate_wms.csv",
        ["Cod articol", "Lot", "Cantitate", "UM"],
        ["DS0001", "L001", "10", "kg"],
    )
    write_csv(
        tmp_path / "rapoarte productie.csv",
        ["Cod produs", "Lot produs", "Cantitate produsa"],
        ["DS0001", "L001", "10"],
    )
    write_minimal_xlsx(
        tmp_path / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Lot", "Denumire"],
        ["DS0001", "L001", "Produs test"],
    )
    write_minimal_xlsx(
        tmp_path / "stoc la moment original.xlsx",
        "Stoc",
        ["Cod articol", "Lot", "Stoc", "UM"],
        ["DS0001", "L001", "5", "kg"],
    )

    traceability_case = traceability_case_to_dict(run_traceability_case(tmp_path, "DS0001", "L001"))

    assert traceability_case["subject"] == {
        "code": "DS0001",
        "lot": "L001",
        "case_type": CASE_FINISHED_PRODUCT,
    }
    assert traceability_case["evidence"]
    assert traceability_case["sections"]["core_validation_status"] == "VALID"
