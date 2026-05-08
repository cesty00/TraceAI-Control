"""Initial source data quality gate for TraceAI Control."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.core.normalized_dataset import (
    NormalizedDataSet,
    NormalizedTable,
    is_code_column,
    is_lot_column,
    is_quantity_column,
)
from src.core.source_discovery import find_official_source_path
from src.core.source_inventory import InventoryReport, SourceInventory, build_inventory_report
from src.quality.models import (
    DataQualityIssue,
    DataQualityReport,
    DataQualitySeverity,
    DataQualitySourceSummary,
    DataQualityStatus,
)

SOURCE_KEYS: dict[str, str] = {
    "trasabilitate_wms.csv": "wms",
    "rapoarte productie.csv": "production",
    "nomenclator.xlsx": "nomenclator",
    "stoc la moment original.xlsx": "stock",
}

REQUIRED_COLUMN_CHECKS: dict[str, tuple[str, ...]] = {
    "wms": ("code", "lot", "quantity"),
    "production": ("code", "lot", "quantity"),
    "stock": ("code", "lot", "quantity"),
    "nomenclator": ("code",),
}

CHECK_LABELS: dict[str, str] = {
    "code": "cod articol/produs",
    "lot": "lot",
    "quantity": "cantitate/stoc",
}


def run_data_quality_gate(source_directory: str | Path, dataset: NormalizedDataSet | None = None, inventory: InventoryReport | None = None) -> DataQualityReport:
    root = Path(source_directory).expanduser().resolve()
    inventory_report = inventory or build_inventory_report(root)
    issues: list[DataQualityIssue] = []

    for source in inventory_report.sources:
        issues.extend(issues_from_inventory_source(source))

    if dataset is not None:
        issues.extend(issues_from_dataset(dataset))

    sources = build_source_summaries(root, inventory_report, dataset)
    status = compute_status(issues)
    return DataQualityReport(
        status=status,
        source_count=len(inventory_report.expected_sources),
        sources_found=sum(1 for source in inventory_report.sources if source.found),
        issues=issues,
        sources=sources,
    )


def issues_from_inventory_source(source: SourceInventory) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    source_key = SOURCE_KEYS.get(source.expected_name, source.expected_name)
    if not source.found:
        issues.append(
            DataQualityIssue(
                severity=DataQualitySeverity.ERROR,
                source_key=source_key,
                source_name=source.expected_name,
                message=f"Lipsește sursa obligatorie: {source.expected_name}.",
            )
        )
    for problem in source.problems:
        severity = DataQualitySeverity.ERROR if not source.found else DataQualitySeverity.WARNING
        issues.append(
            DataQualityIssue(
                severity=severity,
                source_key=source_key,
                source_name=source.expected_name,
                message=problem,
            )
        )
    for sheet in source.sheets:
        for problem in sheet.problems:
            issues.append(
                DataQualityIssue(
                    severity=DataQualitySeverity.WARNING,
                    source_key=source_key,
                    source_name=source.expected_name,
                    sheet_name=sheet.name,
                    message=problem,
                )
            )
    return issues


def issues_from_dataset(dataset: NormalizedDataSet) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    tables_by_source: dict[str, list[NormalizedTable]] = {}
    for table in dataset.tables:
        tables_by_source.setdefault(table.source_key, []).append(table)

    for table in dataset.tables:
        issues.extend(required_column_issues(table, tables_by_source))
        issues.extend(row_quality_issues(table))
        for problem in table.problems:
            issues.append(
                DataQualityIssue(
                    severity=DataQualitySeverity.WARNING,
                    source_key=table.source_key,
                    source_name=table.source_name,
                    sheet_name=table.sheet_name,
                    message=problem,
                )
            )
    for problem in dataset.problems:
        issues.append(
            DataQualityIssue(
                severity=DataQualitySeverity.ERROR if problem.startswith("Lipseste") else DataQualitySeverity.WARNING,
                source_key="dataset",
                source_name="NormalizedDataSet",
                message=problem,
            )
        )
    return issues


def required_column_issues(
    table: NormalizedTable,
    tables_by_source: dict[str, list[NormalizedTable]] | None = None,
) -> list[DataQualityIssue]:
    checks = REQUIRED_COLUMN_CHECKS.get(table.source_key, ())
    missing: list[str] = []
    for check in checks:
        if check == "code" and not any(is_code_column(column.normalized_name) for column in table.columns):
            missing.append(check)
        if check == "lot" and not any(is_lot_column(column.normalized_name) for column in table.columns):
            missing.append(check)
        if check == "quantity" and not any(is_quantity_column(column.normalized_name) for column in table.columns):
            missing.append(check)

    source_tables = tables_by_source or {table.source_key: [table]}
    return [
        DataQualityIssue(
            severity=missing_check_severity(table, check, source_tables),
            source_key=table.source_key,
            source_name=table.source_name,
            sheet_name=table.sheet_name,
            column_name=CHECK_LABELS[check],
            message=f"Lipsește coloana obligatorie pentru {CHECK_LABELS[check]}.",
        )
        for check in missing
    ]


def missing_check_severity(
    table: NormalizedTable,
    check: str,
    tables_by_source: dict[str, list[NormalizedTable]],
) -> DataQualitySeverity:
    if table.source_key == "nomenclator" and check == "code":
        sibling_tables = tables_by_source.get(table.source_key, [])
        if any(
            sibling is not table and any(is_code_column(column.normalized_name) for column in sibling.columns)
            for sibling in sibling_tables
        ):
            return DataQualitySeverity.WARNING
    return DataQualitySeverity.ERROR


def row_quality_issues(table: NormalizedTable) -> list[DataQualityIssue]:
    issues: list[DataQualityIssue] = []
    invalid_quantity_rows = [row.row_number for row in table.rows if any("Cantitate neparsabila" in problem for problem in row.problems)]
    if invalid_quantity_rows:
        issues.append(
            DataQualityIssue(
                severity=DataQualitySeverity.WARNING,
                source_key=table.source_key,
                source_name=table.source_name,
                sheet_name=table.sheet_name,
                message=f"{len(invalid_quantity_rows)} rând(uri) au cantități nenumerice sau neclare.",
                row_count=len(invalid_quantity_rows),
                sample_rows=invalid_quantity_rows[:10],
            )
        )

    missing_code_rows = [row.row_number for row in table.rows if requires_identity(table.source_key) and not row.code_lot_hints.get("code")]
    if missing_code_rows:
        issues.append(
            DataQualityIssue(
                severity=DataQualitySeverity.WARNING,
                source_key=table.source_key,
                source_name=table.source_name,
                sheet_name=table.sheet_name,
                message=f"{len(missing_code_rows)} rând(uri) nu au cod articol/produs identificabil.",
                row_count=len(missing_code_rows),
                sample_rows=missing_code_rows[:10],
            )
        )

    missing_lot_rows = [row.row_number for row in table.rows if requires_lot(table.source_key) and not row.code_lot_hints.get("lot")]
    if missing_lot_rows:
        issues.append(
            DataQualityIssue(
                severity=DataQualitySeverity.WARNING,
                source_key=table.source_key,
                source_name=table.source_name,
                sheet_name=table.sheet_name,
                message=f"{len(missing_lot_rows)} rând(uri) nu au lot identificabil.",
                row_count=len(missing_lot_rows),
                sample_rows=missing_lot_rows[:10],
            )
        )
    return issues


def requires_identity(source_key: str) -> bool:
    return source_key in {"wms", "production", "stock", "nomenclator"}


def requires_lot(source_key: str) -> bool:
    return source_key in {"wms", "production", "stock"}


def build_source_summaries(root: Path, inventory: InventoryReport, dataset: NormalizedDataSet | None) -> list[DataQualitySourceSummary]:
    tables_by_source: dict[str, list[NormalizedTable]] = {}
    if dataset is not None:
        for table in dataset.tables:
            tables_by_source.setdefault(table.source_key, []).append(table)

    summaries: list[DataQualitySourceSummary] = []
    for source in inventory.sources:
        source_key = SOURCE_KEYS.get(source.expected_name, source.expected_name)
        tables = tables_by_source.get(source_key, [])
        path = find_official_source_path(root, source.expected_name) or Path(source.path or root / source.expected_name)
        size = path.stat().st_size if path.exists() and path.is_file() else None
        row_count = source.row_count if source.row_count is not None else sum(table.row_count for table in tables) if tables else None
        column_count = len(source.columns) if source.columns else max((len(table.columns) for table in tables), default=0) or None
        sheet_count = len(source.sheets) if source.sheets else len(tables) if tables and source.file_type == "xlsx" else None
        summaries.append(
            DataQualitySourceSummary(
                source_key=source_key,
                source_name=source.expected_name,
                found=source.found,
                file_size_bytes=size,
                row_count=row_count,
                column_count=column_count,
                sheet_count=sheet_count,
            )
        )
    return summaries


def compute_status(issues: Iterable[DataQualityIssue]) -> DataQualityStatus:
    severities = [issue.severity for issue in issues]
    if any(severity == DataQualitySeverity.ERROR for severity in severities):
        return DataQualityStatus.ERROR
    if any(severity == DataQualitySeverity.WARNING for severity in severities):
        return DataQualityStatus.WARNING
    return DataQualityStatus.OK
