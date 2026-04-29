"""Controlled demo runner for TraceAI Control DOCX generation.

This script builds a synthetic TraceabilityCase and generates a demonstrative
DOCX report without UI and without reading operational source files.

Usage:
    python samples/demo_docx_runner.py --output samples/output/demo_traceability_report.docx
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.core.dataset_validation import ValidationReport
from src.core.normalized_dataset import NormalizedColumn, NormalizedDataSet, NormalizedRow, NormalizedTable
from src.core.record_selection import select_records_by_code_lot
from src.core.run_pipeline import CorePipelineResult
from src.core.source_inventory import InventoryReport
from src.report.docx_minimal import generate_minimal_docx_report
from src.rules.case_type_detection import detect_case_type
from src.rules.run_rules_pipeline import RulesPipelineResult
from src.rules.traceability_case import build_traceability_case

DEMO_CODE = "DS0001"
DEMO_LOT = "L001"


def make_normalized_table(source_key: str, source_name: str, rows: list[dict[str, str]]) -> NormalizedTable:
    """Build a synthetic normalized table for the controlled demo."""

    columns = sorted({column for row in rows for column in row.keys()})
    return NormalizedTable(
        source_key=source_key,
        source_name=source_name,
        sheet_name=None,
        columns=[NormalizedColumn(name, name) for name in columns],
        rows=[
            NormalizedRow(
                row_number=index + 2,
                values=row,
                original_values=row,
                code_lot_hints={"code": row.get("cod", ""), "lot": row.get("lot", "")},
            )
            for index, row in enumerate(rows)
        ],
        row_count=len(rows),
    )


def build_demo_dataset() -> NormalizedDataSet:
    """Return a controlled dataset that exercises the DOCX report sections."""

    return NormalizedDataSet(
        source_directory="samples/demo-controlled-dataset",
        tables=[
            make_normalized_table(
                "production",
                "rapoarte productie.csv",
                [
                    {"cod": DEMO_CODE, "lot": DEMO_LOT, "comandă": "PRD-1", "cantitate": "10", "um": "kg"},
                    {"cod": DEMO_CODE, "lot": DEMO_LOT, "denumire": "Materie primă zahăr", "cantitate": "2", "um": "kg"},
                    {"cod": DEMO_CODE, "lot": DEMO_LOT, "denumire": "Folie ambalaj", "cantitate": "5", "um": "buc"},
                ],
            ),
            make_normalized_table(
                "wms",
                "trasabilitate_wms.csv",
                [
                    {
                        "cod": DEMO_CODE,
                        "lot": DEMO_LOT,
                        "document comanda": "CMD-OUT-1",
                        "client": "Client demo",
                        "cantitate": "4",
                        "um": "kg",
                    }
                ],
            ),
            make_normalized_table(
                "stock",
                "stoc la moment original.xlsx",
                [{"cod": DEMO_CODE, "lot": DEMO_LOT, "stoc": "6", "um": "kg", "locație": "DEP-1"}],
            ),
        ],
    )


def build_demo_traceability_case():
    """Build a TraceabilityCase from the controlled synthetic dataset."""

    dataset = build_demo_dataset()
    selection = select_records_by_code_lot(dataset, DEMO_CODE, DEMO_LOT)
    detection = detect_case_type(dataset, selection, DEMO_CODE, DEMO_LOT)
    core = CorePipelineResult(
        inventory=InventoryReport(source_directory=dataset.source_directory, expected_sources=[], sources=[]),
        normalized_dataset=dataset,
        validation=ValidationReport(status="VALID"),
        selection=selection,
    )
    rules = RulesPipelineResult(core=core, case_type_detection=detection)
    return build_traceability_case(rules, DEMO_CODE, DEMO_LOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a controlled demo DOCX report.")
    parser.add_argument(
        "--output",
        default="samples/output/demo_traceability_report.docx",
        help="Output DOCX path.",
    )
    args = parser.parse_args(argv)

    output = Path(args.output)
    traceability_case = build_demo_traceability_case()
    generate_minimal_docx_report(traceability_case, output)
    print(f"Generated demo DOCX: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
