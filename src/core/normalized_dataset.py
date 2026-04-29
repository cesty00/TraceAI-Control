"""
NormalizedDataSet builder for TraceAI Control Core Engine.

Faza 2 scope:
- load the official source files;
- normalize column names for stable internal access;
- preserve original values and units of measure;
- expose lightweight cod/lot identity hints.

This module intentionally does not calculate traceability, does not classify
case_type and does not build TraceabilityCase. Those steps belong to the Rules
Engine and later phases.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .source_inventory import (
    OFFICIAL_SOURCES,
    XLSX_MAIN_NAMESPACE,
    XLSX_OFFICE_REL_NAMESPACE,
    XLSX_REL_NAMESPACE,
    normalize_xlsx_target,
    read_shared_strings,
    read_text_with_fallback,
    read_workbook_sheets,
    read_xlsx_cell_value,
    xlsx_column_index,
)


SOURCE_KEYS: dict[str, str] = {
    "trasabilitate_wms.csv": "wms",
    "rapoarte productie.csv": "production",
    "nomenclator.xlsx": "nomenclator",
    "stoc la moment original.xlsx": "stock",
}

CODE_HINTS = ("cod", "articol", "produs", "item", "sku")
LOT_HINTS = ("lot", "batch")
QUANTITY_HINTS = ("cant", "cantitate", "qty", "quantity", "stoc")
UM_HINTS = ("um", "u.m", "unitate", "unit", "masura", "măsură")


@dataclass(frozen=True)
class NormalizedColumn:
    """Mapping between original and normalized column name."""

    original_name: str
    normalized_name: str


@dataclass(frozen=True)
class NormalizedRow:
    """One normalized row.

    Values are preserved as text under both original and normalized column
    mappings. Numeric quantity values are exposed separately as Decimal strings
    only when parsing is unambiguous.
    """

    row_number: int
    values: dict[str, str]
    original_values: dict[str, str]
    quantity_values: dict[str, str] = field(default_factory=dict)
    code_lot_hints: dict[str, str] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NormalizedTable:
    """Normalized table extracted from one CSV or XLSX sheet."""

    source_key: str
    source_name: str
    sheet_name: str | None
    columns: list[NormalizedColumn]
    rows: list[NormalizedRow]
    row_count: int
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NormalizedDataSet:
    """Core Engine output for Faza 2."""

    source_directory: str
    tables: list[NormalizedTable]
    problems: list[str] = field(default_factory=list)


def build_normalized_dataset(source_directory: str | Path) -> NormalizedDataSet:
    """Build a normalized dataset from the four official source files."""

    root = Path(source_directory).expanduser().resolve()
    tables: list[NormalizedTable] = []
    problems: list[str] = []

    for source_name in OFFICIAL_SOURCES:
        path = root / source_name
        source_key = SOURCE_KEYS[source_name]

        if not path.exists():
            problems.append(f"Lipseste sursa obligatorie: {source_name}")
            continue

        if path.suffix.lower() == ".csv":
            table = load_csv_table(source_key, source_name, path)
            tables.append(table)
            problems.extend(prefix_problems(source_name, table.problems))
            continue

        if path.suffix.lower() == ".xlsx":
            xlsx_tables, xlsx_problems = load_xlsx_tables(source_key, source_name, path)
            tables.extend(xlsx_tables)
            problems.extend(prefix_problems(source_name, xlsx_problems))
            continue

        problems.append(f"Extensie nesuportata pentru {source_name}: {path.suffix}")

    return NormalizedDataSet(
        source_directory=str(root),
        tables=tables,
        problems=problems,
    )


def load_csv_table(source_key: str, source_name: str, path: Path) -> NormalizedTable:
    """Load and normalize one CSV source."""

    problems: list[str] = []
    try:
        text = read_text_with_fallback(path)
    except (UnicodeDecodeError, OSError) as exc:
        return NormalizedTable(
            source_key=source_key,
            source_name=source_name,
            sheet_name=None,
            columns=[],
            rows=[],
            row_count=0,
            problems=[f"Nu se poate citi CSV-ul: {exc}"],
        )

    if not text.strip():
        return NormalizedTable(
            source_key=source_key,
            source_name=source_name,
            sheet_name=None,
            columns=[],
            rows=[],
            row_count=0,
            problems=["Fisier CSV gol."],
        )

    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
        problems.append("Delimiter CSV nedetectat automat; s-a folosit virgula implicit.")

    raw_rows = list(csv.reader(text.splitlines(), dialect))
    if not raw_rows:
        return NormalizedTable(source_key, source_name, None, [], [], 0, ["CSV fara randuri."])

    original_headers = [value.strip() for value in raw_rows[0]]
    columns = build_columns(original_headers)
    rows = build_rows(columns, raw_rows[1:])
    problems.extend(validate_columns(columns))

    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        problems=problems,
    )


def load_xlsx_tables(source_key: str, source_name: str, path: Path) -> tuple[list[NormalizedTable], list[str]]:
    """Load and normalize all sheets from one XLSX source."""

    problems: list[str] = []
    tables: list[NormalizedTable] = []

    try:
        with zipfile.ZipFile(path) as workbook:
            shared_strings = read_shared_strings(workbook)
            sheet_entries = read_workbook_sheets(workbook)
            if not sheet_entries:
                return [], ["Workbook XLSX fara sheet-uri detectate."]

            for sheet_name, sheet_path in sheet_entries:
                try:
                    table = load_xlsx_sheet(
                        source_key,
                        source_name,
                        sheet_name,
                        sheet_path,
                        workbook,
                        shared_strings,
                    )
                    tables.append(table)
                except KeyError:
                    problems.append(f"Sheet intern lipsa: {sheet_path}")
                except ET.ParseError as exc:
                    problems.append(f"XML invalid in sheet {sheet_name}: {exc}")

    except zipfile.BadZipFile:
        return [], ["Fisier XLSX invalid sau corupt."]
    except (KeyError, ET.ParseError, OSError) as exc:
        return [], [f"Nu se poate citi XLSX-ul: {exc}"]

    return tables, problems


def load_xlsx_sheet(
    source_key: str,
    source_name: str,
    sheet_name: str,
    sheet_path: str,
    workbook: zipfile.ZipFile,
    shared_strings: list[str],
) -> NormalizedTable:
    """Load and normalize one XLSX sheet."""

    root = ET.fromstring(workbook.read(sheet_path))
    namespace = {"x": XLSX_MAIN_NAMESPACE}
    xml_rows = root.findall(".//x:sheetData/x:row", namespace)
    if not xml_rows:
        return NormalizedTable(source_key, source_name, sheet_name, [], [], 0, ["Sheet fara randuri."])

    matrix = [read_xlsx_row(row, shared_strings) for row in xml_rows]
    original_headers = [value.strip() for value in matrix[0]]
    columns = build_columns(original_headers)
    rows = build_rows(columns, matrix[1:])
    problems = validate_columns(columns)

    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=sheet_name,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        problems=problems,
    )


def read_xlsx_row(row: ET.Element, shared_strings: list[str]) -> list[str]:
    """Read one XLSX row into a dense value list."""

    namespace = {"x": XLSX_MAIN_NAMESPACE}
    values_by_column: dict[int, str] = {}
    for cell in row.findall("x:c", namespace):
        reference = cell.attrib.get("r", "")
        values_by_column[xlsx_column_index(reference)] = read_xlsx_cell_value(cell, shared_strings)

    if not values_by_column:
        return []

    return [values_by_column.get(index, "") for index in range(max(values_by_column) + 1)]


def build_columns(original_headers: list[str]) -> list[NormalizedColumn]:
    """Build normalized column mappings while preserving originals."""

    normalized_counts: dict[str, int] = {}
    columns: list[NormalizedColumn] = []

    for index, original in enumerate(original_headers, start=1):
        base = normalize_column_name(original) or f"coloana_{index}"
        count = normalized_counts.get(base, 0) + 1
        normalized_counts[base] = count
        normalized = base if count == 1 else f"{base}_{count}"
        columns.append(NormalizedColumn(original_name=original, normalized_name=normalized))

    return columns


def build_rows(columns: list[NormalizedColumn], raw_rows: list[list[str]]) -> list[NormalizedRow]:
    """Build normalized rows from raw row values."""

    rows: list[NormalizedRow] = []
    for offset, raw_row in enumerate(raw_rows, start=2):
        values: dict[str, str] = {}
        original_values: dict[str, str] = {}
        quantity_values: dict[str, str] = {}
        code_lot_hints: dict[str, str] = {}
        problems: list[str] = []

        for index, column in enumerate(columns):
            value = raw_row[index].strip() if index < len(raw_row) else ""
            values[column.normalized_name] = value
            original_values[column.original_name or column.normalized_name] = value

            if is_quantity_column(column.normalized_name):
                normalized_quantity = normalize_quantity(value)
                if normalized_quantity is not None:
                    quantity_values[column.normalized_name] = normalized_quantity
                elif value:
                    problems.append(f"Cantitate neparsabila in coloana {column.original_name}: {value}")

            if is_code_column(column.normalized_name) and value:
                code_lot_hints.setdefault("code", value)
            if is_lot_column(column.normalized_name) and value:
                code_lot_hints.setdefault("lot", value)

        rows.append(
            NormalizedRow(
                row_number=offset,
                values=values,
                original_values=original_values,
                quantity_values=quantity_values,
                code_lot_hints=code_lot_hints,
                problems=problems,
            )
        )

    return rows


def normalize_column_name(value: str) -> str:
    """Normalize a source column name into a stable snake_case key."""

    text = remove_diacritics(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def normalize_quantity(value: str) -> str | None:
    """Normalize a quantity as a Decimal string when unambiguous."""

    text = value.strip().replace(" ", "")
    if not text:
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return str(Decimal(text))
    except InvalidOperation:
        return None


def remove_diacritics(value: str) -> str:
    """Remove Romanian diacritics for stable technical keys."""

    translation = str.maketrans(
        {
            "ă": "a",
            "â": "a",
            "î": "i",
            "ș": "s",
            "ş": "s",
            "ț": "t",
            "ţ": "t",
            "Ă": "A",
            "Â": "A",
            "Î": "I",
            "Ș": "S",
            "Ş": "S",
            "Ț": "T",
            "Ţ": "T",
        }
    )
    return value.translate(translation)


def validate_columns(columns: list[NormalizedColumn]) -> list[str]:
    """Return early structural problems for a table."""

    problems: list[str] = []
    if not columns:
        problems.append("Nu au fost detectate coloane.")
        return problems

    if not any(is_code_column(column.normalized_name) for column in columns):
        problems.append("Nu a fost detectata nicio coloana probabila de cod articol/produs.")

    if not any(is_lot_column(column.normalized_name) for column in columns):
        problems.append("Nu a fost detectata nicio coloana probabila de lot.")

    return problems


def is_code_column(name: str) -> bool:
    return any(hint in name for hint in CODE_HINTS)


def is_lot_column(name: str) -> bool:
    return any(hint in name for hint in LOT_HINTS)


def is_quantity_column(name: str) -> bool:
    return any(hint in name for hint in QUANTITY_HINTS)


def is_um_column(name: str) -> bool:
    return any(hint in name for hint in UM_HINTS)


def prefix_problems(prefix: str, problems: list[str]) -> list[str]:
    return [f"{prefix}: {problem}" for problem in problems]


def dataset_to_dict(dataset: NormalizedDataSet) -> dict[str, Any]:
    """Convert dataset dataclasses to a JSON-safe dictionary."""

    return asdict(dataset)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Construieste NormalizedDataSet pentru sursele oficiale TraceAI Control."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru output JSON.")
    args = parser.parse_args(argv)

    payload = json.dumps(
        dataset_to_dict(build_normalized_dataset(args.source_directory)),
        ensure_ascii=False,
        indent=2,
    )

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
