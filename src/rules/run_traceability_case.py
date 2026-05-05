from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.errors import (
    AmbiguousCaseTypeError,
    DataQualityBlockingError,
    MissingRequiredColumnError,
    MissingSourceFileError,
    NoMatchingRecordsError,
)
from src.quality.data_quality_gate import run_data_quality_gate
from src.rules.run_rules_pipeline import RulesPipelineResult, run_rules_pipeline
from src.rules.traceability_case import (
    TraceabilityCase,
    build_traceability_case,
    traceability_case_to_dict,
)


BLOCKING_SOURCE_READ_MARKERS = (
    "nu se poate citi",
    "nu se poate decoda",
    "invalid sau corupt",
    "xml invalid",
    "sheet intern lipsa",
)


def run_traceability_case(source_directory: str | Path, code: str, lot: str) -> TraceabilityCase:
    """Run Rules Pipeline and build a minimal TraceabilityCase."""

    rules_result = run_rules_pipeline(source_directory, code, lot)
    raise_typed_traceability_error_if_needed(rules_result, code, lot)
    return build_traceability_case(rules_result, code, lot)


def raise_typed_traceability_error_if_needed(
    rules_result: RulesPipelineResult,
    code: str,
    lot: str,
) -> None:
    """Raise user-actionable errors for the most common blocking failures."""

    quality_report = run_data_quality_gate(
        rules_result.core.normalized_dataset.source_directory,
        dataset=rules_result.core.normalized_dataset,
        inventory=rules_result.core.inventory,
    )

    if quality_report.sources_found == 0:
        raise MissingSourceFileError(
            user_message="Nu pot genera raportul: nu am găsit sursele oficiale în folderul selectat.",
            technical_detail=(
                "Nu a fost identificată nicio sursă oficială. "
                f"Surse așteptate: {', '.join(rules_result.core.inventory.expected_sources)}"
            ),
            recommended_action="Selectează folderul care conține sursele oficiale TraceAI Control și reîncearcă.",
        )

    missing_column_issues = [
        issue
        for issue in quality_report.issues
        if issue.severity.value == "ERROR" and "coloana obligatorie" in issue.message.casefold()
    ]
    if missing_column_issues and not rules_result.core.selection.records:
        details = []
        for issue in missing_column_issues[:5]:
            location = issue.source_name
            if issue.sheet_name:
                location = f"{location} / {issue.sheet_name}"
            if issue.column_name:
                details.append(f"{location}: {issue.column_name}")
            else:
                details.append(f"{location}: {issue.message}")
        raise MissingRequiredColumnError(
            user_message="Nu pot genera raportul: una sau mai multe surse nu au coloanele obligatorii.",
            technical_detail="Coloane lipsă detectate: " + "; ".join(details),
            recommended_action="Reexportă sursele cu layout-ul standard și verifică prezența coloanelor pentru cod, lot și cantitate.",
        )

    blocking_source_read_issues = collect_blocking_source_read_issues(quality_report)
    if blocking_source_read_issues and not rules_result.core.selection.records:
        raise DataQualityBlockingError(
            user_message="Nu pot genera raportul: una sau mai multe surse oficiale sunt corupte sau nu pot fi citite.",
            technical_detail="Probleme de citire detectate: " + "; ".join(blocking_source_read_issues[:5]),
            recommended_action="Reexportă sursa afectată și înlocuiește fișierul corupt înainte de a reîncerca.",
        )

    if not rules_result.core.selection.records:
        raise NoMatchingRecordsError(
            user_message="Nu pot genera raportul: nu am găsit date pentru codul și lotul cerute.",
            technical_detail=f"Căutare fără rezultate pentru cod={code!r}, lot={lot!r}.",
            recommended_action="Verifică valorile introduse și confirmă că produsul și lotul există în sursele selectate.",
        )

    if rules_result.case_type_detection.case_type == "UNKNOWN":
        observations = rules_result.case_type_detection.observations or [
            "Detectorul de tip de caz nu a returnat suficiente dovezi pentru clasificare."
        ]
        raise AmbiguousCaseTypeError(
            user_message="Nu pot genera raportul: cazul nu poate fi clasificat în mod sigur din datele disponibile.",
            technical_detail=(
                f"Clasificare ambiguă pentru cod={code!r}, lot={lot!r}. "
                f"Observații detector: {' | '.join(observations)}"
            ),
            recommended_action=(
                "Verifică sursele selectate și confirmă dacă articolul trebuie tratat ca produs finit, "
                "materie primă sau caz WMS-only."
            ),
        )


def collect_blocking_source_read_issues(quality_report: object) -> list[str]:
    """Return deduplicated source read issues that should block generation."""

    details: list[str] = []
    seen: set[str] = set()

    for issue in quality_report.issues:
        message = issue.message.casefold()
        if not any(marker in message for marker in BLOCKING_SOURCE_READ_MARKERS):
            continue

        location = issue.source_name
        if issue.sheet_name:
            location = f"{location} / {issue.sheet_name}"
        detail = f"{location}: {issue.message}"
        if detail in seen:
            continue

        seen.add(detail)
        details.append(detail)

    return details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Construieste TraceabilityCase minimal pentru TraceAI Control."
    )
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("code")
    parser.add_argument("lot")
    args = parser.parse_args(argv)

    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    print(json.dumps(traceability_case_to_dict(traceability_case), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
