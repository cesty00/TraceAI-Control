import zipfile
from pathlib import Path

from src.core.normalized_dataset import build_normalized_dataset
from src.quality.data_quality_gate import run_data_quality_gate


def test_nomenclator_auxiliary_sheet_without_code_is_warning_when_primary_sheet_is_valid(tmp_path: Path) -> None:
    write_minimal_csv_sources(tmp_path)
    write_multi_sheet_xlsx(
        tmp_path / "nomenclator.xlsx",
        [
            ("Sheet", ["Cod articol", "Denumire"], [["DS0001", "Produs test"]]),
            ("Sheet2", ["Baza"], [["aux"]]),
        ],
    )
    write_single_sheet_xlsx(tmp_path / "stoc la moment original.xlsx", "Sheet", ["cod", "lot", "stoc"], [["DS0001", "L001", "5"]])

    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset)

    auxiliary_issue = next(
        issue
        for issue in report.issues
        if issue.source_name == "nomenclator.xlsx"
        and issue.sheet_name == "Sheet2"
        and issue.column_name == "cod articol/produs"
        and issue.message == "Lipsește coloana obligatorie pentru cod articol/produs."
    )
    assert auxiliary_issue.severity.value == "WARNING"
    assert report.error_count == 0
    assert report.status.value == "WARNING"


def test_nomenclator_single_unusable_sheet_keeps_error(tmp_path: Path) -> None:
    write_minimal_csv_sources(tmp_path)
    write_single_sheet_xlsx(tmp_path / "nomenclator.xlsx", "Sheet", ["Baza"], [["aux"]])
    write_single_sheet_xlsx(tmp_path / "stoc la moment original.xlsx", "Sheet", ["cod", "lot", "stoc"], [["DS0001", "L001", "5"]])

    dataset = build_normalized_dataset(tmp_path)
    report = run_data_quality_gate(tmp_path, dataset=dataset)

    code_issue = next(
        issue
        for issue in report.issues
        if issue.source_name == "nomenclator.xlsx"
        and issue.column_name == "cod articol/produs"
        and issue.message == "Lipsește coloana obligatorie pentru cod articol/produs."
    )
    assert code_issue.severity.value == "ERROR"
    assert report.error_count == 1
    assert report.status.value == "ERROR"


def test_data_quality_summary_contains_textual_issue_list(tmp_path: Path) -> None:
    write_minimal_csv_sources(tmp_path)
    write_single_sheet_xlsx(tmp_path / "nomenclator.xlsx", "Sheet", ["Baza"], [["aux"]])
    write_single_sheet_xlsx(tmp_path / "stoc la moment original.xlsx", "Sheet", ["cod", "lot", "stoc"], [["DS0001", "L001", "5"]])

    report = run_data_quality_gate(tmp_path, dataset=build_normalized_dataset(tmp_path))
    summary = report.compact_summary()

    assert summary["error_count"] == 1
    assert summary["issue_count"] >= 1
    assert summary["issues"]
    assert set(summary["issues"][0]) == {"severity", "source_name", "sheet_name", "column_name", "message"}


def write_minimal_csv_sources(folder: Path) -> None:
    (folder / "trasabilitate_wms.csv").write_text(
        "cod,lot,cantitate,um,document\nDS0001,L001,10,kg,WMS-1\n",
        encoding="utf-8",
    )
    (folder / "rapoarte productie.csv").write_text(
        "cod,lot,cantitate,um,comanda\nDS0001,L001,10,kg,PRD-1\n",
        encoding="utf-8",
    )


def write_single_sheet_xlsx(path: Path, sheet_name: str, headers: list[str], rows: list[list[str]]) -> None:
    write_multi_sheet_xlsx(path, [(sheet_name, headers, rows)])


def write_multi_sheet_xlsx(path: Path, sheets: list[tuple[str, list[str], list[list[str]]]]) -> None:
    def cell(column: str, row_number: int, value: str) -> str:
        return f'<c r="{column}{row_number}" t="inlineStr"><is><t>{value}</t></is></c>'

    workbook_sheets: list[str] = []
    rel_entries: list[str] = []
    sheet_files: dict[str, str] = {}

    for index, (sheet_name, headers, rows) in enumerate(sheets, start=1):
        workbook_sheets.append(f'<sheet name="{sheet_name}" sheetId="{index}" r:id="rId{index}"/>')
        rel_entries.append(
            '<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet{index}.xml"/>'.format(index=index)
        )
        row_xml_parts = [
            f'<row r="1">{"".join(cell(chr(ord("A") + column_index), 1, value) for column_index, value in enumerate(headers))}</row>'
        ]
        for row_index, row in enumerate(rows, start=2):
            row_xml_parts.append(
                f'<row r="{row_index}">{"".join(cell(chr(ord("A") + column_index), row_index, value) for column_index, value in enumerate(row))}</row>'
            )
        sheet_files[f"xl/worksheets/sheet{index}.xml"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(row_xml_parts)}</sheetData>'
            "</worksheet>"
        )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(rel_entries)}'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("xl/workbook.xml", workbook_xml)
        package.writestr("xl/_rels/workbook.xml.rels", rels_xml)
        for filename, content in sheet_files.items():
            package.writestr(filename, content)
