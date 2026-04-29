"""
Structural validation for TraceAI Control NormalizedDataSet.

Faza 2 scope only:
- validate that official source tables were loaded;
- validate that each table has rows and columns;
- validate probable code and lot columns;
- surface row-level parsing problems already detected by Core.

This module intentionally does not classify cases, does not calculate balances
and does not build TraceabilityCase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .normalized_dataset import (
    NormalizedDataSet,
    NormalizedTable,
    build_normalized_dataset,
    is_code_column,
    is_lot_column,
)


@dataclass(frozen=True)
class ValidationIssue:
    """One structural validation issue."""

    severity: str
    source_key: str | None
    source_name: str | None
    sheet_name: str | None
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Validation result for a NormalizedDataSet."""

    status: str
    issues: list[ValidationIssue] = field(default_factory=list)


def validate_normalized_dataset(dataset: NormalizedDataSet) -> ValidationReport:
    """Validate only structural readiness of a NormalizedDataSet."""

    issues: list[ValidationIssue] = []

    for problem in dataset.problems:
        issues.append(
            ValidationIssue(
                severity="ERROR",
                source_key=None,
                source_name=None,
                sheet_name=None,
                message=problem,
            )
        )

    if not dataset.tables:
        issues.append(
            ValidationIssue(
                severity="ERROR",
                source_key=None,
                source_name=None,
                sheet_name=None,
                message="NormalizedDataSet nu contine tabele.",
            )
        )

    for table in dataset.tables:
        issues.extend(validate_table(table))

    status = "VALID" if not any(issue.severity == "ERROR" for issue in issues) else "INVALID"
    return ValidationReport(status=status, issues=issues)


def validate_table(table: NormalizedTable) -> list[ValidationIssue]:
    """Validate one normalized table structurally."""

    issues: list[ValidationIssue] = []

    for problem in table.problems:
        issues.append(make_issue("WARNING", table, problem))

    if not table.columns:
        issues.append(make_issue("ERROR", table, "Tabel fara coloane detectate."))
        return issues

    if table.row_count == 0:
        issues.append(make_issue("WARNING", table, "Tabel fara randuri de date."))

    if not any(is_code_column(column.normalized_name) for column in table.columns):
        issues.append(make_issue("WARNING", table, "Lipseste coloana probabila de cod articol/produs."))

    if not any(is_lot_column(column.normalized_name) for column in table.columns):
        issues.append(make_issue("WARNING", table, "Lipseste coloana probabila de lot."))

    for row in table.rows:
        for problem in row.problems:
            issues.append(make_issue("WARNING", table, f"Rand {row.row_number}: {problem}"))

    return issues


def make_issue(severity: str, table: NormalizedTable, message: str) -> ValidationIssue:
    return ValidationIssue(
        severity=severity,
        source_key=table.source_key,
        source_name=table.source_name,
        sheet_name=table.sheet_name,
        message=message,
    )


def validation_report_to_dict(report: ValidationReport) -> dict[str, Any]:
    """Convert validation report dataclasses to a JSON-safe dictionary."""

    return asdict(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valideaza structural NormalizedDataSet pentru sursele TraceAI Control."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru raport JSON.")
    args = parser.parse_args(argv)

    dataset = build_normalized_dataset(args.source_directory)
    report = validate_normalized_dataset(dataset)
    payload = json.dumps(validation_report_to_dict(report), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if report.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
