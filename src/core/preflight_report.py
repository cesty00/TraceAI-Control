"""Preflight report for TraceAI Control UI and diagnostics.

The preflight layer summarizes whether the official operational sources are
available and whether the requested code/lot can be found before report
generation. It does not build a traceability case and does not calculate audit
results.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.core.build_info import BuildInfo, build_info_to_dict, get_build_info
from src.core.normalized_dataset import build_normalized_dataset
from src.core.record_selection import RecordSelectionResult, select_records_by_code_lot
from src.core.source_inventory import SourceInventory, build_inventory_report

STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_BLOCKER = "BLOCKER"

PRIMARY_SUBJECT_SOURCES = {"production", "wms"}
OPTIONAL_SUBJECT_SOURCES = {"stock", "nomenclator"}


@dataclass(frozen=True)
class PreflightSourceStatus:
    """UI-ready status for one official source."""

    source_key: str
    expected_name: str
    display_name: str
    status: str
    found: bool
    path: str | None
    file_type: str | None
    row_count: int | None = None
    sheet_count: int = 0
    sheet_names: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PreflightSubjectStatus:
    """UI-ready status for the requested code/lot."""

    code: str
    lot: str
    status: str
    total_records: int
    records_by_source: dict[str, int]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PreflightReport:
    """Top-level preflight report."""

    schema_version: str
    source_directory: str
    build_info: dict[str, Any]
    sources: list[PreflightSourceStatus]
    subject: PreflightSubjectStatus
    status: str
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def build_preflight_report(
    source_directory: str | Path,
    code: str,
    lot: str,
    build_info: BuildInfo | None = None,
) -> PreflightReport:
    """Build a UI/diagnostic preflight report for source folder + code/lot."""

    metadata = build_info or get_build_info()
    inventory = build_inventory_report(source_directory)
    dataset = build_normalized_dataset(source_directory)
    selection = select_records_by_code_lot(dataset, code, lot)

    sources = [source_status_from_inventory(source) for source in inventory.sources]
    subject = subject_status_from_selection(selection)

    warnings: list[str] = []
    blockers: list[str] = []

    for source in sources:
        if source.status == STATUS_BLOCKER:
            blockers.extend(f"{source.display_name}: {problem}" for problem in source.problems or ["sursă indisponibilă"])
        elif source.status == STATUS_WARNING:
            warnings.extend(f"{source.display_name}: {problem}" for problem in source.problems or ["observație sursă"])

    warnings.extend(dataset.problems)
    warnings.extend(selection.warnings)
    subject_warnings, subject_blockers = evaluate_subject_coverage(subject.records_by_source)
    warnings.extend(subject_warnings)
    blockers.extend(subject_blockers)

    if subject.total_records == 0:
        blockers.append("Codul și lotul nu au fost găsite în sursele normalizate.")

    status = STATUS_BLOCKER if blockers else STATUS_WARNING if warnings else STATUS_OK

    return PreflightReport(
        schema_version="preflight-report.v1",
        source_directory=str(Path(source_directory).expanduser().resolve()),
        build_info=build_info_to_dict(metadata),
        sources=sources,
        subject=subject,
        status=status,
        warnings=deduplicate(warnings),
        blockers=deduplicate(blockers),
    )


def evaluate_subject_coverage(records_by_source: dict[str, int]) -> tuple[list[str], list[str]]:
    """Evaluate where the requested code/lot was found.

    Stocul este validare finală, nu sursă de adevăr pentru existența cazului.
    Un cod+lot poate lipsi din stoc dacă nu mai există stoc fizic la momentul
    analizat. De aceea lipsa din `stock` este observație, nu blocaj.
    """

    warnings: list[str] = []
    blockers: list[str] = []

    missing_primary = sorted(source for source in PRIMARY_SUBJECT_SOURCES if records_by_source.get(source, 0) == 0)
    if len(missing_primary) == len(PRIMARY_SUBJECT_SOURCES):
        blockers.append("Codul și lotul nu au fost găsite în sursele principale PRD/WMS.")
    else:
        for source in missing_primary:
            warnings.append(f"Codul și lotul nu au fost găsite în sursa principală {source}.")

    if records_by_source.get("stock", 0) == 0:
        warnings.append("Codul și lotul nu apar în stocul la moment; acest lucru poate fi normal dacă nu există stoc fizic pe codul și lotul analizat.")

    if records_by_source.get("nomenclator", 0) == 0:
        warnings.append("Codul și lotul nu apar împreună în nomenclator; nomenclatorul poate conține doar codul, fără lot.")

    return warnings, blockers


def source_status_from_inventory(source: SourceInventory) -> PreflightSourceStatus:
    source_key = source_key_for_expected_name(source.expected_name)
    display_name = display_name_for_source(source.expected_name)
    sheet_names = [sheet.name for sheet in source.sheets]
    sheet_count = len(source.sheets)
    row_count = source.row_count
    if row_count is None and source.sheets:
        known_rows = [sheet.row_count for sheet in source.sheets if sheet.row_count is not None]
        row_count = sum(known_rows) if known_rows else None

    if not source.found:
        status = STATUS_BLOCKER
    elif source.problems or any(sheet.problems for sheet in source.sheets):
        status = STATUS_WARNING
    else:
        status = STATUS_OK

    problems = list(source.problems)
    for sheet in source.sheets:
        problems.extend(f"{sheet.name}: {problem}" for problem in sheet.problems)

    return PreflightSourceStatus(
        source_key=source_key,
        expected_name=source.expected_name,
        display_name=display_name,
        status=status,
        found=source.found,
        path=source.path,
        file_type=source.file_type,
        row_count=row_count,
        sheet_count=sheet_count,
        sheet_names=sheet_names,
        problems=deduplicate(problems),
    )


def subject_status_from_selection(selection: RecordSelectionResult) -> PreflightSubjectStatus:
    counts = Counter(record.source_key for record in selection.records)
    status = STATUS_OK if selection.records else STATUS_BLOCKER
    return PreflightSubjectStatus(
        code=selection.input_code,
        lot=selection.input_lot,
        status=status,
        total_records=len(selection.records),
        records_by_source=dict(sorted(counts.items())),
        warnings=selection.warnings,
    )


def source_key_for_expected_name(expected_name: str) -> str:
    mapping = {
        "trasabilitate_wms.csv": "wms",
        "rapoarte productie.csv": "production",
        "nomenclator.xlsx": "nomenclator",
        "stoc la moment original.xlsx": "stock",
    }
    return mapping.get(expected_name, expected_name)


def display_name_for_source(expected_name: str) -> str:
    mapping = {
        "trasabilitate_wms.csv": "WMS trasabilitate",
        "rapoarte productie.csv": "Raport producție PRD",
        "nomenclator.xlsx": "Nomenclator",
        "stoc la moment original.xlsx": "Stoc la moment",
    }
    return mapping.get(expected_name, expected_name)


def deduplicate(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def preflight_report_to_dict(report: PreflightReport) -> dict[str, Any]:
    return asdict(report)


def format_preflight_report(report: PreflightReport) -> str:
    """Format a compact text summary for UI fallback/diagnostics."""

    lines = [
        f"Preflight status: {report.status}",
        f"Folder surse: {report.source_directory}",
        f"Produs/Lot: {report.subject.code} / {report.subject.lot}",
        f"Rânduri găsite pentru cod+lot: {report.subject.total_records}",
        "",
        "Surse:",
    ]
    for source in report.sources:
        detail = f"{source.display_name}: {source.status}"
        if source.found:
            detail += f" | {source.file_type or ''} | rânduri={source.row_count if source.row_count is not None else 'n/a'}"
            if source.sheet_count:
                detail += f" | sheet-uri={source.sheet_count}"
        else:
            detail += " | lipsă"
        lines.append(detail)
        if source.path:
            lines.append(f"  path: {source.path}")
        for problem in source.problems:
            lines.append(f"  problemă: {problem}")

    if report.subject.records_by_source:
        lines.append("")
        lines.append("Cod+lot pe surse:")
        for source_key, count in report.subject.records_by_source.items():
            lines.append(f"  {source_key}: {count}")

    if report.blockers:
        lines.append("")
        lines.append("Blocaje:")
        lines.extend(f"- {item}" for item in report.blockers)

    if report.warnings:
        lines.append("")
        lines.append("Avertizări:")
        lines.extend(f"- {item}" for item in report.warnings)

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generează raport preflight pentru surse și cod/lot.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs căutat.")
    parser.add_argument("--lot", required=True, help="Lot căutat.")
    parser.add_argument("--output", "-o", help="Cale opțională pentru output JSON.")
    parser.add_argument("--text", action="store_true", help="Afișează sumar text în loc de JSON.")
    args = parser.parse_args(argv)

    report = build_preflight_report(args.source_directory, args.code, args.lot)
    if args.text:
        payload = format_preflight_report(report)
    else:
        payload = json.dumps(preflight_report_to_dict(report), ensure_ascii=False, indent=2) + "\n"

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    return 0 if report.status != STATUS_BLOCKER else 1


if __name__ == "__main__":
    raise SystemExit(main())
