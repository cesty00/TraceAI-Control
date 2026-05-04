from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from src.core.normalized_dataset import build_normalized_dataset
from src.core.source_inventory import build_inventory_report
from src.quality.data_quality_gate import run_data_quality_gate


def write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_xlsx(path: Path, rows: list[list[str]]) -> None:
    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row):
            column = chr(ord("A") + column_index)
            cells.append(f'<c r="{column}{row_index}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    with ZipFile(path, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
""",
        )
        workbook.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
""",
        )
        workbook.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
""",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
""",
        )
        workbook.writestr(
            "xl/worksheets/sheet1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>
""",
        )


def write_minimal_sources(root: Path) -> None:
    write_csv(root / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate,UM\nDS0001,L001,10,kg\n")
    write_csv(root / "rapoarte productie.csv", "Cod produs,Lot,Cantitate,UM\nDS0001,L001,10,kg\n")
    write_xlsx(root / "stoc la moment original.xlsx", [["Cod articol", "Lot", "Stoc", "UM"], ["DS0001", "L001", "5", "kg"]])
    write_xlsx(root / "nomenclator.xlsx", [["Cod articol", "Denumire"], ["DS0001", "Produs test"]])


def test_data_quality_gate_reports_missing_source_file(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate\nDS0001,L001,10\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.status.value == "ERROR"
    assert any("Lipsește sursa obligatorie" in issue.message for issue in report.issues)


def test_data_quality_gate_reports_missing_required_column(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Cantitate\nDS0001,10\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.status.value == "ERROR"
    assert any(issue.source_key == "wms" and "lot" in issue.message.casefold() for issue in report.issues)


def test_data_quality_gate_reports_invalid_quantity(tmp_path: Path) -> None:
    write_csv(tmp_path / "trasabilitate_wms.csv", "Cod articol,Lot,Cantitate\nDS0001,L001,abc\n")

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert any(issue.source_key == "wms" and "cantități" in issue.message for issue in report.issues)
    invalid_issue = next(issue for issue in report.issues if issue.source_key == "wms" and "cantități" in issue.message)
    assert invalid_issue.row_count == 1
    assert invalid_issue.sample_rows == [2]


def test_data_quality_gate_accepts_valid_minimal_dataset(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)

    inventory = build_inventory_report(tmp_path)
    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset, inventory=inventory)

    assert report.compact_summary()["status"] in {"OK", "WARNING"}
    assert report.compact_summary()["source_count"] == 4
    assert report.compact_summary()["sources_found"] == 4
