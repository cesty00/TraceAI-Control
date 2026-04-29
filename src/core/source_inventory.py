"""
Core source inventory for TraceAI Control.

Faza 2 goal:
- read the four official operational sources;
- report files found / missing;
- report XLSX sheets, detected columns, row counts;
- report early structural problems.

This module intentionally does not calculate traceability and does not build
TraceabilityCase. It is a neutral inventory layer for later Core/Rules work.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


OFFICIAL_SOURCES: tuple[str, ...] = (
    "trasabilitate_wms.csv",
    "rapoarte productie.csv",
    "nomenclator.xlsx",
    "stoc la moment original.xlsx",
)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
XLSX_MAIN_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_REL_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
XLSX_OFFICE_REL_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


@dataclass(frozen=True)
class SheetInventory:
    """Inventory for one XLSX sheet."""

    name: str
    columns: list[str] = field(default_factory=list)
    row_count: int | None = None
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceInventory:
    """Inventory for one expected source file."""

    expected_name: str
    path: str | None
    found: bool
    file_type: str | None
    row_count: int | None = None
    columns: list[str] = field(default_factory=list)
    sheets: list[SheetInventory] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InventoryReport:
    """Top-level inventory report."""

    source_directory: str
    expected_sources: list[str]
    sources: list[SourceInventory]
    problems: list[str] = field(default_factory=list)


def build_inventory_report(source_directory: str | Path) -> InventoryReport:
    """Build an inventory report for the official source files.

    The function only inspects file structure. It does not infer traceability,
    does not classify cases and does not reconcile stock.
    """

    root = Path(source_directory).expanduser().resolve()
    source_reports: list[SourceInventory] = []

    for expected_name in OFFICIAL_SOURCES:
        path = root / expected_name
        source_reports.append(inventory_source(expected_name, path))

    global_problems = [
        f"Lipseste sursa obligatorie: {item.expected_name}"
        for item in source_reports
        if not item.found
    ]

    return InventoryReport(
        source_directory=str(root),
        expected_sources=list(OFFICIAL_SOURCES),
        sources=source_reports,
        problems=global_problems,
    )


def inventory_source(expected_name: str, path: Path) -> SourceInventory:
    """Inventory one expected source."""

    extension = path.suffix.lower()

    if not path.exists():
        return SourceInventory(
            expected_name=expected_name,
            path=str(path),
            found=False,
            file_type=extension.lstrip(".") or None,
            problems=["Fisier negasit."],
        )

    if not path.is_file():
        return SourceInventory(
            expected_name=expected_name,
            path=str(path),
            found=False,
            file_type=extension.lstrip(".") or None,
            problems=["Calea exista, dar nu este fisier."],
        )

    if extension not in SUPPORTED_EXTENSIONS:
        return SourceInventory(
            expected_name=expected_name,
            path=str(path),
            found=True,
            file_type=extension.lstrip(".") or None,
            problems=[f"Extensie nesuportata: {extension or '<fara extensie>'}."],
        )

    if extension == ".csv":
        row_count, columns, problems = inspect_csv(path)
        return SourceInventory(
            expected_name=expected_name,
            path=str(path),
            found=True,
            file_type="csv",
            row_count=row_count,
            columns=columns,
            problems=problems,
        )

    sheets, problems = inspect_xlsx(path)
    return SourceInventory(
        expected_name=expected_name,
        path=str(path),
        found=True,
        file_type="xlsx",
        sheets=sheets,
        problems=problems,
    )


def inspect_csv(path: Path) -> tuple[int | None, list[str], list[str]]:
    """Inspect a CSV file and return row count, header columns and problems."""

    problems: list[str] = []
    try:
        text = read_text_with_fallback(path)
    except UnicodeDecodeError as exc:
        return None, [], [f"Nu se poate decoda CSV-ul: {exc}."]
    except OSError as exc:
        return None, [], [f"Nu se poate citi CSV-ul: {exc}."]

    if not text.strip():
        return 0, [], ["Fisier CSV gol."]

    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
        problems.append("Delimiter CSV nedetectat automat; s-a folosit virgula implicit.")

    rows = list(csv.reader(text.splitlines(), dialect))
    if not rows:
        return 0, [], ["Fisier CSV fara randuri citibile."]

    columns = normalize_columns(rows[0])
    if not columns:
        problems.append("Header CSV fara coloane detectabile.")

    duplicated = find_duplicates(columns)
    if duplicated:
        problems.append(f"Coloane duplicate in header CSV: {', '.join(duplicated)}.")

    return max(len(rows) - 1, 0), columns, problems


def inspect_xlsx(path: Path) -> tuple[list[SheetInventory], list[str]]:
    """Inspect an XLSX file without requiring third-party dependencies."""

    problems: list[str] = []
    try:
        with zipfile.ZipFile(path) as workbook:
            shared_strings = read_shared_strings(workbook)
            sheet_entries = read_workbook_sheets(workbook)
            sheets: list[SheetInventory] = []

            for sheet_name, sheet_path in sheet_entries:
                try:
                    columns, row_count, sheet_problems = inspect_xlsx_sheet(
                        workbook,
                        sheet_path,
                        shared_strings,
                    )
                except KeyError:
                    columns, row_count, sheet_problems = [], None, [
                        f"Fisierul intern al sheet-ului lipseste: {sheet_path}."
                    ]

                sheets.append(
                    SheetInventory(
                        name=sheet_name,
                        columns=columns,
                        row_count=row_count,
                        problems=sheet_problems,
                    )
                )

            if not sheets:
                problems.append("Workbook XLSX fara sheet-uri detectate.")

            return sheets, problems
    except zipfile.BadZipFile:
        return [], ["Fisier XLSX invalid sau corupt."]
    except ET.ParseError as exc:
        return [], [f"XML XLSX invalid: {exc}."]
    except OSError as exc:
        return [], [f"Nu se poate citi XLSX-ul: {exc}."]


def read_text_with_fallback(path: Path) -> str:
    """Read text using common encodings used in operational exports."""

    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1250", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    return path.read_text()


def read_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    """Read XLSX shared strings."""

    try:
        raw_xml = workbook.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(raw_xml)
    namespace = {"x": XLSX_MAIN_NAMESPACE}
    values: list[str] = []

    for item in root.findall("x:si", namespace):
        text_parts = [node.text or "" for node in item.findall(".//x:t", namespace)]
        values.append("".join(text_parts))

    return values


def read_workbook_sheets(workbook: zipfile.ZipFile) -> list[tuple[str, str]]:
    """Return pairs of sheet name and internal worksheet path."""

    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))

    rel_targets: dict[str, str] = {}
    for rel in rels_root.findall(f"{{{XLSX_REL_NAMESPACE}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type", "")
        if rel_id and target and rel_type.endswith("/worksheet"):
            rel_targets[rel_id] = normalize_xlsx_target(target)

    namespace = {
        "x": XLSX_MAIN_NAMESPACE,
        "r": XLSX_OFFICE_REL_NAMESPACE,
    }

    sheets: list[tuple[str, str]] = []
    for sheet in workbook_root.findall(".//x:sheet", namespace):
        name = sheet.attrib.get("name", "FARA_NUME")
        rel_id = sheet.attrib.get(f"{{{XLSX_OFFICE_REL_NAMESPACE}}}id")
        if rel_id and rel_id in rel_targets:
            sheets.append((name, rel_targets[rel_id]))

    return sheets


def inspect_xlsx_sheet(
    workbook: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> tuple[list[str], int, list[str]]:
    """Inspect one XLSX sheet."""

    root = ET.fromstring(workbook.read(sheet_path))
    namespace = {"x": XLSX_MAIN_NAMESPACE}
    rows = root.findall(".//x:sheetData/x:row", namespace)
    if not rows:
        return [], 0, ["Sheet fara randuri."]

    header_values = read_xlsx_row_values(rows[0], shared_strings)
    columns = normalize_columns(header_values)
    problems: list[str] = []

    if not columns:
        problems.append("Header XLSX fara coloane detectabile.")

    duplicated = find_duplicates(columns)
    if duplicated:
        problems.append(f"Coloane duplicate in header XLSX: {', '.join(duplicated)}.")

    return columns, max(len(rows) - 1, 0), problems


def read_xlsx_row_values(row: ET.Element, shared_strings: list[str]) -> list[str]:
    """Read cell values from one XLSX row."""

    namespace = {"x": XLSX_MAIN_NAMESPACE}
    cells = row.findall("x:c", namespace)

    values_by_column: dict[int, str] = {}
    for cell in cells:
        reference = cell.attrib.get("r", "")
        column_index = xlsx_column_index(reference)
        values_by_column[column_index] = read_xlsx_cell_value(cell, shared_strings)

    if not values_by_column:
        return []

    return [
        values_by_column.get(index, "")
        for index in range(max(values_by_column) + 1)
    ]


def read_xlsx_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    """Read a single XLSX cell value."""

    namespace = {"x": XLSX_MAIN_NAMESPACE}
    cell_type = cell.attrib.get("t")

    inline_text = cell.find(".//x:is/x:t", namespace)
    if inline_text is not None:
        return inline_text.text or ""

    value = cell.find("x:v", namespace)
    raw_value = value.text if value is not None else ""

    if cell_type == "s":
        try:
            return shared_strings[int(raw_value)]
        except (ValueError, IndexError):
            return raw_value

    return raw_value or ""


def normalize_columns(values: Iterable[Any]) -> list[str]:
    """Normalize header values for stable downstream use."""

    return [str(value).strip() for value in values if str(value).strip()]


def find_duplicates(values: Iterable[str]) -> list[str]:
    """Return duplicate values while preserving first duplicate order."""

    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(key)
    return duplicates


def normalize_xlsx_target(target: str) -> str:
    """Normalize relationship target to a Zip path."""

    target = target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return f"xl/{target}"


def xlsx_column_index(reference: str) -> int:
    """Return zero-based column index from an XLSX cell reference."""

    letters = re.sub(r"[^A-Za-z]", "", reference).upper()
    if not letters:
        return 0

    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return index - 1


def report_to_dict(report: InventoryReport) -> dict[str, Any]:
    """Convert report dataclasses to a JSON-safe dictionary."""

    return asdict(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventariaza sursele operationale oficiale TraceAI Control."
    )
    parser.add_argument(
        "source_directory",
        help="Folderul care contine cele patru surse oficiale.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Cale optionala pentru raport JSON. Daca lipseste, raportul se afiseaza in consola.",
    )

    args = parser.parse_args(argv)
    report = report_to_dict(build_inventory_report(args.source_directory))
    payload = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
