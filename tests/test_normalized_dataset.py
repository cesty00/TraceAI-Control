import csv
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.normalized_dataset import build_normalized_dataset, dataset_to_dict


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


def write_csv(path: Path, headers: list[str], row: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerow(row)


def test_normalized_dataset_preserves_values_and_builds_hints(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "trasabilitate_wms.csv",
        ["Cod articol", "Lot", "Cantitate", "UM"],
        ["DS0001", "L001", "10,50", "kg"],
    )
    write_csv(
        tmp_path / "rapoarte productie.csv",
        ["Cod produs", "Lot produs", "Cantitate produsa"],
        ["DS0001", "L001", "25"],
    )
    write_minimal_xlsx(
        tmp_path / "nomenclator.xlsx",
        "Articole",
        ["Cod", "Denumire", "Categorie"],
        ["DS0001", "Produs test", "PF"],
    )
    write_minimal_xlsx(
        tmp_path / "stoc la moment original.xlsx",
        "Stoc",
        ["Cod articol", "Lot", "Stoc", "UM"],
        ["DS0001", "L001", "5.5", "kg"],
    )

    dataset = dataset_to_dict(build_normalized_dataset(tmp_path))

    assert dataset["problems"] == []
    assert len(dataset["tables"]) == 4

    wms = dataset["tables"][0]
    assert wms["source_key"] == "wms"
    assert [column["normalized_name"] for column in wms["columns"]] == ["cod_articol", "lot", "cantitate", "um"]
    assert wms["rows"][0]["values"]["cantitate"] == "10,50"
    assert wms["rows"][0]["quantity_values"]["cantitate"] == "10.50"
    assert wms["rows"][0]["code_lot_hints"] == {"code": "DS0001", "lot": "L001"}


def test_normalized_dataset_prefers_real_article_code_over_numeric_article_id(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", ["Cod articol", "Lot"], ["DS0001", "L001"])
    write_csv(
        tmp_path / "rapoarte productie.csv",
        ["PRE_ID Articol", "PRE_Cod Articol", "PRE_LOT"],
        ["2070", "DS0001", "L001"],
    )
    write_minimal_xlsx(tmp_path / "nomenclator.xlsx", "Articole", ["Cod", "Lot"], ["DS0001", "L001"])
    write_minimal_xlsx(tmp_path / "stoc la moment original.xlsx", "Stoc", ["Cod articol", "Lot"], ["DS0001", "L001"])

    dataset = dataset_to_dict(build_normalized_dataset(tmp_path))
    production = dataset["tables"][1]

    assert production["rows"][0]["code_lot_hints"] == {"code": "DS0001", "lot": "L001"}


def test_normalized_dataset_reports_missing_files(tmp_path: Path) -> None:
    dataset = dataset_to_dict(build_normalized_dataset(tmp_path))

    assert dataset["tables"] == []
    assert len(dataset["problems"]) == 4
