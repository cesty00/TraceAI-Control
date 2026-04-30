"""Generate a multi-case reference matrix from real TraceAI sources.

This diagnostic script avoids overfitting the engine to a single product. It
uses the independent reference extractor on several representative code+lot
pairs discovered from WMS and PRD.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from samples.discover_traceability_cases import discover_cases
from samples.extract_reference_traceability import extract_reference, reference_to_jsonable


DEFAULT_FINISHED_LIMIT = 4
DEFAULT_COMPONENT_LIMIT = 4
DEFAULT_WMS_ONLY_LIMIT = 4


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate multi-case TraceAI reference matrix.")
    parser.add_argument("source_directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--finished-limit", type=int, default=DEFAULT_FINISHED_LIMIT)
    parser.add_argument("--component-limit", type=int, default=DEFAULT_COMPONENT_LIMIT)
    parser.add_argument("--wms-only-limit", type=int, default=DEFAULT_WMS_ONLY_LIMIT)
    args = parser.parse_args(argv)

    source_dir = Path(args.source_directory)
    matrix = build_matrix(source_dir, args.finished_limit, args.component_limit, args.wms_only_limit)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(matrix_to_markdown(matrix), encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated reference case matrix: {output}")
    return 0


def build_matrix(source_dir: Path, finished_limit: int, component_limit: int, wms_only_limit: int) -> dict[str, object]:
    discovery = discover_cases(source_dir, max(finished_limit, component_limit, wms_only_limit, 15))
    selected_cases: list[dict[str, str]] = []
    selected_cases.extend(select_cases("finished_product_candidate", discovery["finished_product_candidates"], finished_limit))
    selected_cases.extend(select_cases("component_candidate", discovery["component_candidates"], component_limit))
    selected_cases.extend(select_cases("wms_only_candidate", discovery["wms_only_candidates"], wms_only_limit))
    selected_cases = deduplicate_cases(selected_cases)

    references: list[dict[str, object]] = []
    for case in selected_cases:
        reference = reference_to_jsonable(extract_reference(source_dir, case["code"], case["lot"]))
        references.append(
            {
                "selection_category": case["selection_category"],
                "selection_name": case.get("name", ""),
                "code": case["code"],
                "lot": case["lot"],
                "summary": summarize_reference(reference),
                "reference": reference,
            }
        )

    return {
        "source_directory": str(source_dir),
        "selected_case_count": len(references),
        "selection_limits": {
            "finished": finished_limit,
            "component": component_limit,
            "wms_only": wms_only_limit,
        },
        "cases": references,
    }


def select_cases(category: str, rows: object, limit: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in list(rows)[:limit]:
        code = str(row.get("code", "")).strip()
        lot = str(row.get("lot", "")).strip()
        if not code or not lot:
            continue
        selected.append(
            {
                "selection_category": category,
                "code": code,
                "lot": lot,
                "name": str(row.get("name", "")).strip(),
            }
        )
    return selected


def deduplicate_cases(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for case in cases:
        key = (case["code"], case["lot"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def summarize_reference(reference: dict[str, object]) -> dict[str, object]:
    prd_production = reference.get("prd_production_totals", [])
    raw_materials = reference.get("prd_raw_materials", [])
    packaging = reference.get("prd_packaging", [])
    auxiliaries = reference.get("prd_auxiliaries", [])
    deliveries = reference.get("wms_delivery_totals", [])
    return {
        "case_type_hint": infer_case_type_hint(reference),
        "wms_rows": reference.get("wms_rows", 0),
        "prd_rows": reference.get("prd_rows", 0),
        "stock_found": reference.get("stock_found"),
        "production_order_count": len(prd_production),
        "raw_material_count": len(raw_materials),
        "packaging_count": len(packaging),
        "auxiliary_count": len(auxiliaries),
        "delivery_count": len(deliveries),
    }


def infer_case_type_hint(reference: dict[str, object]) -> str:
    if int(reference.get("prd_rows", 0) or 0) > 0:
        return "FINISHED_PRODUCT"
    if int(reference.get("wms_rows", 0) or 0) > 0:
        return "WMS_ONLY_OR_INPUT"
    return "UNKNOWN"


def matrix_to_markdown(matrix: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# TraceAI reference case matrix")
    lines.append("")
    lines.append(f"Source directory: `{matrix['source_directory']}`")
    lines.append(f"Selected cases: {matrix['selected_case_count']}")
    lines.append("")
    lines.append("## Case overview")
    lines.append("")
    lines.append("| category | code | lot | name | type hint | WMS rows | PRD rows | stock | production orders | raw materials | packaging | auxiliary | deliveries |")
    lines.append("| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |")
    for case in matrix["cases"]:
        summary = case["summary"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(case["selection_category"]),
                    str(case["code"]),
                    str(case["lot"]),
                    str(case.get("selection_name", "")),
                    str(summary["case_type_hint"]),
                    str(summary["wms_rows"]),
                    str(summary["prd_rows"]),
                    str(summary["stock_found"]),
                    str(summary["production_order_count"]),
                    str(summary["raw_material_count"]),
                    str(summary["packaging_count"]),
                    str(summary["auxiliary_count"]),
                    str(summary["delivery_count"]),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Suggested regression coverage")
    lines.append("")
    lines.append("Use this matrix to choose a stable set of cases covering:")
    lines.append("- finished product with PRD production and WMS deliveries")
    lines.append("- second finished product, different lot/order pattern")
    lines.append("- raw material/input component")
    lines.append("- packaging component")
    lines.append("- auxiliary/gas component")
    lines.append("- WMS-only case")
    lines.append("- case with stock correction")
    lines.append("- case absent from stock")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
