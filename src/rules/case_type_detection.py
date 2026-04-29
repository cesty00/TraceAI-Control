"""
Case type detection for TraceAI Control Rules Engine.

Faza 3 scope only:
- receive Core Engine output;
- inspect selected records and normalized tables;
- classify the requested code + lot as one of the supported case types;
- explain the decision with source evidence.

This module intentionally does not calculate traceability, does not apply stock
balances and does not build TraceabilityCase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.core.normalized_dataset import NormalizedDataSet, NormalizedTable, build_normalized_dataset
from src.core.record_selection import RecordSelectionResult, select_records_by_code_lot


CASE_FINISHED_PRODUCT = "FINISHED_PRODUCT"
CASE_RAW_MATERIAL = "RAW_MATERIAL"
CASE_WMS_ONLY_PRODUCT = "WMS_ONLY_PRODUCT"
CASE_UNKNOWN = "UNKNOWN"

PRODUCTION_SOURCE_KEY = "production"
WMS_SOURCE_KEY = "wms"
NOMENCLATOR_SOURCE_KEY = "nomenclator"
STOCK_SOURCE_KEY = "stock"

RAW_MATERIAL_HINTS = (
    "materie prima",
    "materii prime",
    "raw material",
    "mp",
)
FINISHED_PRODUCT_HINTS = (
    "produs finit",
    "finished product",
    "pf",
)


@dataclass(frozen=True)
class CaseTypeEvidence:
    """One evidence item used for case type detection."""

    source_key: str
    source_name: str
    sheet_name: str | None
    row_number: int | None
    message: str


@dataclass(frozen=True)
class CaseTypeDetectionResult:
    """Rules Engine result for the first Faza 3 step."""

    input_code: str
    input_lot: str
    case_type: str
    evidence: list[CaseTypeEvidence] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)


def detect_case_type(
    dataset: NormalizedDataSet,
    selection: RecordSelectionResult,
    code: str,
    lot: str,
) -> CaseTypeDetectionResult:
    """Detect case type using only normalized Core Engine data."""

    evidence: list[CaseTypeEvidence] = []
    observations: list[str] = []

    production_matches = [record for record in selection.records if record.source_key == PRODUCTION_SOURCE_KEY]
    wms_matches = [record for record in selection.records if record.source_key == WMS_SOURCE_KEY]
    nomenclator_matches = [record for record in selection.records if record.source_key == NOMENCLATOR_SOURCE_KEY]

    if production_matches:
        evidence.extend(
            make_record_evidence(
                production_matches,
                "Codul si lotul apar in sursa de productie; cazul este tratat ca produs finit.",
            )
        )
        return CaseTypeDetectionResult(
            input_code=code,
            input_lot=lot,
            case_type=CASE_FINISHED_PRODUCT,
            evidence=evidence,
            observations=observations,
        )

    classification = classify_from_nomenclator_values(nomenclator_matches)
    if classification == CASE_RAW_MATERIAL:
        evidence.extend(
            make_record_evidence(
                nomenclator_matches,
                "Nomenclatorul indica articol de tip materie prima.",
            )
        )
        return CaseTypeDetectionResult(code, lot, CASE_RAW_MATERIAL, evidence, observations)

    if classification == CASE_FINISHED_PRODUCT:
        evidence.extend(
            make_record_evidence(
                nomenclator_matches,
                "Nomenclatorul indica articol de tip produs finit, dar nu exista productie pentru lotul cautat.",
            )
        )
        observations.append("Nu au fost gasite randuri de productie pentru codul si lotul cautate.")
        return CaseTypeDetectionResult(code, lot, CASE_WMS_ONLY_PRODUCT, evidence, observations)

    if wms_matches:
        evidence.extend(
            make_record_evidence(
                wms_matches,
                "Codul si lotul apar in WMS, dar nu apar in productie sau clasificare suficienta.",
            )
        )
        return CaseTypeDetectionResult(code, lot, CASE_WMS_ONLY_PRODUCT, evidence, observations)

    observations.append("Nu exista suficiente date pentru detectarea tipului de caz.")
    return CaseTypeDetectionResult(code, lot, CASE_UNKNOWN, evidence, observations)


def classify_from_nomenclator_values(records: list[Any]) -> str | None:
    """Infer article class from nomenclator row values when available."""

    for record in records:
        combined_values = " ".join(record.values.values()).casefold()
        if any(hint in combined_values for hint in RAW_MATERIAL_HINTS):
            return CASE_RAW_MATERIAL
        if any(hint in combined_values for hint in FINISHED_PRODUCT_HINTS):
            return CASE_FINISHED_PRODUCT
    return None


def make_record_evidence(records: list[Any], message: str) -> list[CaseTypeEvidence]:
    """Build evidence items from selected records."""

    return [
        CaseTypeEvidence(
            source_key=record.source_key,
            source_name=record.source_name,
            sheet_name=record.sheet_name,
            row_number=record.row_number,
            message=message,
        )
        for record in records
    ]


def detect_case_type_from_dataset(dataset: NormalizedDataSet, code: str, lot: str) -> CaseTypeDetectionResult:
    """Convenience wrapper that selects records before detecting case type."""

    selection = select_records_by_code_lot(dataset, code, lot)
    return detect_case_type(dataset, selection, code, lot)


def case_type_result_to_dict(result: CaseTypeDetectionResult) -> dict[str, Any]:
    """Convert detection result dataclasses to a JSON-safe dictionary."""

    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detecteaza case_type din datele Core Engine.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", help="Cale optionala pentru rezultat JSON.")
    args = parser.parse_args(argv)

    dataset = build_normalized_dataset(args.source_directory)
    result = detect_case_type_from_dataset(dataset, args.code, args.lot)
    payload = json.dumps(case_type_result_to_dict(result), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if result.case_type != CASE_UNKNOWN else 1


if __name__ == "__main__":
    raise SystemExit(main())
