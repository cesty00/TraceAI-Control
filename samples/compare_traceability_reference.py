"""Compare independent reference extraction with the real TraceabilityCase.

The script is intended for GitHub Actions diagnostics. It keeps development from
overfitting to one visual DOCX by asserting that the app-populated
TraceabilityCase contains the same key PRD/WMS values as the independent
reference extractor.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from samples.extract_reference_traceability import extract_reference, reference_to_jsonable
from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import TraceabilityCase, TraceabilityReportTable


COMPARISON_TOLERANCE = Decimal("0.000001")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare reference extraction with TraceabilityCase tables.")
    parser.add_argument("source_directory")
    parser.add_argument("--code", required=True)
    parser.add_argument("--lot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)

    reference = reference_to_jsonable(extract_reference(Path(args.source_directory), args.code, args.lot))
    case = run_traceability_case(args.source_directory, args.code, args.lot)
    result = compare_reference_with_case(reference, case)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(comparison_to_markdown(result), encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated reference comparison: {output}")
    if result["status"] != "PASS":
        for problem in result["problems"]:
            print(f"PROBLEM: {problem}")
        return 1
    return 0


def compare_reference_with_case(reference: dict[str, Any], case: TraceabilityCase) -> dict[str, Any]:
    problems: list[str] = []
    checks: list[dict[str, Any]] = []

    checks.append(check_count("production_order_count", len(reference["prd_production_totals"]), len(case.report_tables.production.rows), problems))
    checks.append(check_count("raw_material_count", len(reference["prd_raw_materials"]), len(case.report_tables.raw_materials.rows), problems))
    checks.append(check_count("packaging_count", len(reference["prd_packaging"]), len(case.report_tables.packaging.rows), problems))
    checks.append(check_count("auxiliary_count", len(reference["prd_auxiliaries"]), len(case.report_tables.auxiliaries_gas.rows), problems))
    checks.append(check_count("delivery_count", len(reference["wms_delivery_totals"]), len(case.report_tables.finished_goods_deliveries.rows), problems))

    expected_production = totals_by_key(reference["prd_production_totals"], ["comanda", "um"], "cantitate")
    actual_production = table_totals_by_key(case.report_tables.production, ["Comandă", "UM"], "Cantitate")
    checks.append(check_totals("production_totals", expected_production, actual_production, problems))

    expected_raw = totals_by_key(reference["prd_raw_materials"], ["cod", "lot", "um"], "cantitate_consumata")
    actual_raw = table_totals_by_key(case.report_tables.raw_materials, ["Cod", "Lot", "UM"], "Cantitate")
    checks.append(check_totals("raw_material_totals", expected_raw, actual_raw, problems))

    expected_packaging = totals_by_key(reference["prd_packaging"], ["cod", "lot", "um"], "cantitate_consumata")
    actual_packaging = table_totals_by_key(case.report_tables.packaging, ["Cod", "Lot", "UM"], "Cantitate")
    checks.append(check_totals("packaging_totals", expected_packaging, actual_packaging, problems))

    expected_aux = totals_by_key(reference["prd_auxiliaries"], ["cod", "lot", "um"], "cantitate_consumata")
    actual_aux = table_totals_by_key(case.report_tables.auxiliaries_gas, ["Cod", "Lot", "UM"], "Cantitate")
    checks.append(check_totals("auxiliary_totals", expected_aux, actual_aux, problems))

    expected_deliveries = totals_by_key(reference["wms_delivery_totals"], ["numar_comanda", "document_comanda", "um"], "total")
    actual_deliveries = table_totals_by_key(case.report_tables.finished_goods_deliveries, ["Numar comanda", "Document comanda", "UM"], "Cantitate")
    checks.append(check_totals("delivery_totals", expected_deliveries, actual_deliveries, problems))

    return {
        "code": reference["code"],
        "lot": reference["lot"],
        "status": "PASS" if not problems else "FAIL",
        "problems": problems,
        "checks": checks,
        "traceability_case_subject": asdict(case.subject),
    }


def check_count(name: str, expected: int, actual: int, problems: list[str]) -> dict[str, Any]:
    ok = expected == actual
    if not ok:
        problems.append(f"{name}: expected {expected}, actual {actual}")
    return {"name": name, "expected": expected, "actual": actual, "status": "PASS" if ok else "FAIL"}


def check_totals(name: str, expected: dict[str, Decimal], actual: dict[str, Decimal], problems: list[str]) -> dict[str, Any]:
    expected_keys = set(expected)
    actual_keys = set(actual)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    mismatched: list[dict[str, str]] = []
    for key in sorted(expected_keys & actual_keys):
        if abs(expected[key] - actual[key]) > COMPARISON_TOLERANCE:
            mismatched.append({"key": key, "expected": format_decimal(expected[key]), "actual": format_decimal(actual[key])})
    if missing or extra or mismatched:
        problems.append(f"{name}: missing={missing}, extra={extra}, mismatched={mismatched}")
    return {
        "name": name,
        "expected": {key: format_decimal(value) for key, value in sorted(expected.items())},
        "actual": {key: format_decimal(value) for key, value in sorted(actual.items())},
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched,
        "status": "PASS" if not missing and not extra and not mismatched else "FAIL",
    }


def totals_by_key(rows: list[dict[str, Any]], key_columns: list[str], quantity_column: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        quantity = parse_decimal(row.get(quantity_column))
        if quantity is None:
            continue
        key = " | ".join(str(row.get(column, "")).strip() for column in key_columns)
        totals[key] = totals.get(key, Decimal("0")) + quantity
    return totals


def table_totals_by_key(table: TraceabilityReportTable, key_columns: list[str], quantity_column: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in table.rows:
        quantity = parse_decimal(row.values.get(quantity_column))
        if quantity is None:
            continue
        key = " | ".join(str(row.values.get(column, "")).strip() for column in key_columns)
        totals[key] = totals.get(key, Decimal("0")) + quantity
    return totals


def parse_decimal(value: object) -> Decimal | None:
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def comparison_to_markdown(result: dict[str, Any]) -> str:
    lines = ["# TraceAI reference comparison", ""]
    lines.append(f"Code: `{result['code']}`")
    lines.append(f"Lot: `{result['lot']}`")
    lines.append(f"Status: **{result['status']}**")
    lines.append("")
    if result["problems"]:
        lines.append("## Problems")
        for problem in result["problems"]:
            lines.append(f"- {problem}")
        lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| check | status |")
    lines.append("| --- | --- |")
    for check in result["checks"]:
        lines.append(f"| {check['name']} | {check['status']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
