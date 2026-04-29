"""
Record selection utilities for TraceAI Control Core Engine.

Faza 2 scope only:
- locate normalized rows that match an operator-provided code and lot;
- preserve the source/table/row context for later Rules Engine steps.

This module intentionally does not classify case_type, does not calculate
traceability and does not build TraceabilityCase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .normalized_dataset import NormalizedDataSet, NormalizedRow, NormalizedTable, build_normalized_dataset


@dataclass(frozen=True)
class SelectedRecord:
    """One normalized row selected by code + lot."""

    source_key: str
    source_name: str
    sheet_name: str | None
    row_number: int
    code: str
    lot: str
    values: dict[str, str]
    original_values: dict[str, str]
    quantity_values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RecordSelectionResult:
    """Selection result across the whole NormalizedDataSet."""

    input_code: str
    input_lot: str
    records: list[SelectedRecord]
    warnings: list[str] = field(default_factory=list)


def select_records_by_code_lot(
    dataset: NormalizedDataSet,
    code: str,
    lot: str,
) -> RecordSelectionResult:
    """Select all rows whose code and lot hints match the requested values."""

    normalized_code = normalize_match_value(code)
    normalized_lot = normalize_match_value(lot)
    records: list[SelectedRecord] = []
    warnings: list[str] = []

    if not normalized_code:
        warnings.append("Codul de cautare este gol.")
    if not normalized_lot:
        warnings.append("Lotul de cautare este gol.")

    if not normalized_code or not normalized_lot:
        return RecordSelectionResult(input_code=code, input_lot=lot, records=[], warnings=warnings)

    for table in dataset.tables:
        table_records = select_records_from_table(table, normalized_code, normalized_lot)
        records.extend(table_records)

    if not records:
        warnings.append("Nu au fost gasite randuri pentru codul si lotul cautate.")

    return RecordSelectionResult(
        input_code=code,
        input_lot=lot,
        records=records,
        warnings=warnings,
    )


def select_records_from_table(
    table: NormalizedTable,
    normalized_code: str,
    normalized_lot: str,
) -> list[SelectedRecord]:
    """Select matching rows from one table."""

    records: list[SelectedRecord] = []
    for row in table.rows:
        row_code = normalize_match_value(row.code_lot_hints.get("code", ""))
        row_lot = normalize_match_value(row.code_lot_hints.get("lot", ""))

        if row_code == normalized_code and row_lot == normalized_lot:
            records.append(build_selected_record(table, row))

    return records


def build_selected_record(table: NormalizedTable, row: NormalizedRow) -> SelectedRecord:
    """Build a selected record while preserving row context."""

    return SelectedRecord(
        source_key=table.source_key,
        source_name=table.source_name,
        sheet_name=table.sheet_name,
        row_number=row.row_number,
        code=row.code_lot_hints.get("code", ""),
        lot=row.code_lot_hints.get("lot", ""),
        values=row.values,
        original_values=row.original_values,
        quantity_values=row.quantity_values,
    )


def normalize_match_value(value: str) -> str:
    """Normalize operator and source values for exact technical matching."""

    return " ".join(str(value).strip().casefold().split())


def selection_result_to_dict(result: RecordSelectionResult) -> dict[str, Any]:
    """Convert selection result dataclasses to a JSON-safe dictionary."""

    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Selecteaza randuri din NormalizedDataSet dupa cod si lot."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru rezultat JSON.")
    args = parser.parse_args(argv)

    dataset = build_normalized_dataset(args.source_directory)
    result = select_records_by_code_lot(dataset, args.code, args.lot)
    payload = json.dumps(selection_result_to_dict(result), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if result.records else 1


if __name__ == "__main__":
    raise SystemExit(main())
