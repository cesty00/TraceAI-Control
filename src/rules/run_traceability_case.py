"""
TraceabilityCase runner for TraceAI Control.

This runner executes the Rules Pipeline and returns the minimal
TraceabilityCase contract that will later feed the DOCX report.

It intentionally does not calculate detailed traceability and does not generate
DOCX.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.rules.run_rules_pipeline import run_rules_pipeline
from src.rules.traceability_case import (
    TraceabilityCase,
    build_traceability_case,
    traceability_case_to_json,
)


def run_traceability_case(source_directory: str | Path, code: str, lot: str) -> TraceabilityCase:
    """Run Rules Pipeline and build a minimal TraceabilityCase."""

    rules_result = run_rules_pipeline(source_directory, code, lot)
    return build_traceability_case(rules_result, code, lot)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Construieste TraceabilityCase minimal pentru TraceAI Control."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru rezultat JSON.")
    args = parser.parse_args(argv)

    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    payload = traceability_case_to_json(traceability_case)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if traceability_case.subject.case_type != "UNKNOWN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
