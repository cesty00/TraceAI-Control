"""
Core Engine pipeline runner for TraceAI Control.

Faza 2 scope only:
- inventory official sources;
- build NormalizedDataSet;
- validate the dataset structurally;
- select rows for operator-provided code + lot.

This module intentionally does not calculate traceability, does not classify
case_type and does not build TraceabilityCase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .dataset_validation import ValidationReport, validate_normalized_dataset
from .normalized_dataset import NormalizedDataSet, build_normalized_dataset
from .record_selection import RecordSelectionResult, select_records_by_code_lot
from .source_inventory import InventoryReport, build_inventory_report


@dataclass(frozen=True)
class CorePipelineResult:
    """Combined result for the Faza 2 Core Engine pipeline."""

    inventory: InventoryReport
    normalized_dataset: NormalizedDataSet
    validation: ValidationReport
    selection: RecordSelectionResult


def run_core_pipeline(source_directory: str | Path, code: str, lot: str) -> CorePipelineResult:
    """Run the Core Engine Faza 2 steps in order."""

    inventory = build_inventory_report(source_directory)
    normalized_dataset = build_normalized_dataset(source_directory)
    validation = validate_normalized_dataset(normalized_dataset)
    selection = select_records_by_code_lot(normalized_dataset, code, lot)

    return CorePipelineResult(
        inventory=inventory,
        normalized_dataset=normalized_dataset,
        validation=validation,
        selection=selection,
    )


def pipeline_result_to_dict(result: CorePipelineResult) -> dict[str, Any]:
    """Convert pipeline result dataclasses to a JSON-safe dictionary."""

    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ruleaza pipeline-ul Core Engine Faza 2 pentru TraceAI Control."
    )
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru rezultat JSON.")
    args = parser.parse_args(argv)

    result = run_core_pipeline(args.source_directory, args.code, args.lot)
    payload = json.dumps(pipeline_result_to_dict(result), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if result.validation.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
