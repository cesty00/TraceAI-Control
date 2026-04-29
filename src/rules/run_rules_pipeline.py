"""
Rules Engine pipeline runner for TraceAI Control.

Faza 3 scope only:
- run the existing Core Engine pipeline;
- detect case_type from the Core output;
- return a combined result for later TraceabilityCase work.

This module intentionally does not calculate traceability, does not apply stock
balances and does not build TraceabilityCase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.core.run_pipeline import CorePipelineResult, run_core_pipeline
from src.rules.case_type_detection import CaseTypeDetectionResult, detect_case_type


@dataclass(frozen=True)
class RulesPipelineResult:
    """Combined Core + Rules result for Faza 3."""

    core: CorePipelineResult
    case_type_detection: CaseTypeDetectionResult


def run_rules_pipeline(source_directory: str | Path, code: str, lot: str) -> RulesPipelineResult:
    """Run Core Engine and the first Rules Engine step."""

    core_result = run_core_pipeline(source_directory, code, lot)
    case_type_detection = detect_case_type(
        core_result.normalized_dataset,
        core_result.selection,
        code,
        lot,
    )

    return RulesPipelineResult(
        core=core_result,
        case_type_detection=case_type_detection,
    )


def rules_pipeline_result_to_dict(result: RulesPipelineResult) -> dict[str, Any]:
    """Convert Rules pipeline result dataclasses to a JSON-safe dictionary."""

    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ruleaza pipeline-ul Rules Engine Faza 3 pentru TraceAI Control."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru rezultat JSON.")
    args = parser.parse_args(argv)

    result = run_rules_pipeline(args.source_directory, args.code, args.lot)
    payload = json.dumps(rules_pipeline_result_to_dict(result), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if result.case_type_detection.case_type != "UNKNOWN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
