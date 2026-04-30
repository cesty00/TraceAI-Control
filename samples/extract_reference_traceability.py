"""Independent reference extractor for TraceAI source files.

This script reads the raw operational files and produces a human-checkable
reference report for one code + lot. It is intentionally separate from the app
pipeline so expected results can be verified before business mapping is coded.

Usage:
    python samples/extract_reference_traceability.py <source_directory> --code DS099903883 --lot 105.26 --output diagnostics/reference_traceability.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


@dataclass
class QuantityTotal:
    unit: str
    total: Decimal = Decimal("0")
    rows: int = 0

    def add(self, quantity: Decimal) -> None:
        self.total += quantity
        self.rows += 1


@dataclass
class ReferenceResult:
    code: str
    lot: str
    source_directory: str
    wms_rows: int = 0
    prd_rows: int = 0
    wms_operation_totals: list[dict[str, str]] = field(default_factory=list)
    wms_delivery_totals: list[dict[str, str]] = field(default_factory=list)
    wms_production_out_totals: list[dict[str, str]] = field(default_factory=list)
    prd_production_totals: list[dict[str, str]] = field(default_factory=list)
    prd_raw_materials: list[dict[str, str]] = field(default_factory=list)
    prd_packaging: list[dict[str, str]] = field(default_factory=list)
    prd_auxiliaries: list[dict[str, str]] = field(default_factory=list)
    stock_found: bool | None = None
    notes: list[str] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract reference traceability values from raw sources.")
    parser.add_argument("source_directory")
    parser.add_argument("--code", required=True)
    parser.add_argument("--lot", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json-output")
    args = parser.parse_args(argv)

    source_dir = Path(args.source_directory)
    result = extract_reference(source_dir, args.code, args.lot)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(reference_to_markdown(result), encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(reference_to_jsonable(result), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated reference report: {output}")
    return 0


def extract_reference(source_dir: Path, code: str, lot: str) -> ReferenceResult:
    result = ReferenceResult(code=code, lot=lot, source_directory=str(source_dir))

    wms_path = source_dir / "trasabilitate_wms.csv"
    prd_path = source_dir / "rapoarte productie.csv"
    stock_path = source_dir / "stoc la moment original.xlsx"

    if wms_path.exists():
        extract_wms_reference(wms_path, result)
    else:
        result.notes.append("WMS source missing: trasabilitate_wms.csv")

    if prd_path.exists():
        extract_prd_reference(prd_path, result)
    else:
        result.notes.append("PRD source missing: rapoarte productie.csv")

    if stock_path.exists():
        result.stock_found = check_stock_presence(stock_path, code, lot)
    else:
        result.stock_found = None
        result.notes.append("Stock source missing: stoc la moment original.xlsx")

    return result


def extract_wms_reference(path: Path, result: ReferenceResult) -> None:
    rows = [row for row in read_csv_dicts(path) if clean(row.get("Cod articol")) == result.code and clean(row.get("Lot")) == result.lot]
    result.wms_rows = len(rows)

    operation_totals: dict[tuple[str, str, str], QuantityTotal] = {}
    delivery_totals: dict[tuple[str, str, str, str], QuantityTotal] = {}
    production_totals: dict[tuple[str, str], QuantityTotal] = {}

    for row in rows:
        quantity = parse_decimal(row.get("Cantitate"))
        if quantity is None:
            continue
        unit = clean(row.get("UM")) or "FARA_UM"
        operation = clean(row.get("Tip operatiune")) or "FARA_OPERATIUNE"
        reason = clean(row.get("Cod-motiv")) or ""
        operation_key = (operation, reason, unit)
        operation_totals.setdefault(operation_key, QuantityTotal(unit)).add(quantity)

        if operation.casefold() == "livrare":
            key = (
                clean(row.get("Numar comanda")),
                clean(row.get("Document comanda")),
                clean(row.get("Partener")),
                unit,
            )
            delivery_totals.setdefault(key, QuantityTotal(unit)).add(quantity)

        if operation.casefold() == "ajustare pozitiva" and reason.casefold() == "production-out":
            order = clean(row.get("Numar comanda")) or clean(row.get("Document intrare")) or clean(row.get("Document comanda"))
            key = (order, unit)
            production_totals.setdefault(key, QuantityTotal(unit)).add(quantity)

    result.wms_operation_totals = [
        {
            "tip_operatiune": operation,
            "cod_motiv": reason,
            "um": total.unit,
            "total": format_decimal(total.total),
            "rows": str(total.rows),
        }
        for (operation, reason, _unit), total in sorted(operation_totals.items())
    ]
    result.wms_delivery_totals = [
        {
            "numar_comanda": order,
            "document_comanda": document,
            "client": partner,
            "um": total.unit,
            "total": format_decimal(total.total),
            "rows": str(total.rows),
        }
        for (order, document, partner, _unit), total in sorted(delivery_totals.items())
    ]
    result.wms_production_out_totals = [
        {
            "comanda": order,
            "um": total.unit,
            "total": format_decimal(total.total),
            "rows": str(total.rows),
        }
        for (order, _unit), total in sorted(production_totals.items())
    ]


def extract_prd_reference(path: Path, result: ReferenceResult) -> None:
    rows = [row for row in read_csv_dicts(path) if clean(row.get("PRE_Cod Articol")) == result.code and clean(row.get("PRE_LOT")) == result.lot]
    result.prd_rows = len(rows)

    production_by_order: dict[tuple[str, str], dict[str, str]] = {}
    components: dict[tuple[str, str, str, str], dict[str, object]] = {}
    control_seen: dict[tuple[str, str, str, str, str, str], Decimal] = {}

    for row in rows:
        order = clean(row.get("Numar Comanda"))
        pre_unit = clean(row.get("PRE_U.M."))
        production_by_order[(order, pre_unit)] = {
            "comanda": order,
            "cod": clean(row.get("PRE_Cod Articol")),
            "lot": clean(row.get("PRE_LOT")),
            "denumire": clean(row.get("PRE_Denumire Articol")),
            "cantitate": clean(row.get("PRE_Cantitate Predare")),
            "um": pre_unit,
            "greutate_control": clean(row.get("Greutate PRE_Articol_Totala(KG)")),
        }

        component_key = (
            clean(row.get("CON_Cod Articol")),
            clean(row.get("CON_LOT")),
            clean(row.get("CON_Denumire Articol")),
            clean(row.get("CON_U.M.")),
        )
        if not component_key[0]:
            continue
        bucket = components.setdefault(
            component_key,
            {
                "rows": 0,
                "consumed": Decimal("0"),
                "orders": set(),
                "control_by_order": defaultdict(Decimal),
            },
        )
        bucket["rows"] = int(bucket["rows"]) + 1
        bucket["orders"].add(order)
        consumed = parse_decimal(row.get("CON_Cantitate Consumata"))
        if consumed is not None:
            bucket["consumed"] = bucket["consumed"] + consumed

        control = parse_decimal(row.get("Greutate CON_Articol_Totala(KG)"))
        if control is not None:
            control_key = component_key + (order, format_decimal(control))
            if control_key not in control_seen:
                control_seen[control_key] = control
                bucket["control_by_order"][order] += control

    result.prd_production_totals = sorted(production_by_order.values(), key=lambda item: item["comanda"])

    raw_materials: list[dict[str, str]] = []
    packaging: list[dict[str, str]] = []
    auxiliaries: list[dict[str, str]] = []

    for (component_code, component_lot, name, unit), bucket in components.items():
        item = {
            "cod": component_code,
            "lot": component_lot,
            "denumire": name,
            "cantitate_consumata": format_decimal(bucket["consumed"]),
            "um": unit,
            "greutate_control_deduplicata": format_decimal(sum(bucket["control_by_order"].values(), Decimal("0"))),
            "comenzi": ", ".join(sorted(bucket["orders"])),
            "rows": str(bucket["rows"]),
        }
        if is_auxiliary(component_code, name):
            auxiliaries.append(item)
        elif is_food_raw_material(component_code, name):
            raw_materials.append(item)
        else:
            packaging.append(item)

    result.prd_raw_materials = sorted(raw_materials, key=lambda item: (item["cod"], item["lot"]))
    result.prd_packaging = sorted(packaging, key=lambda item: (item["cod"], item["lot"]))
    result.prd_auxiliaries = sorted(auxiliaries, key=lambda item: (item["cod"], item["lot"]))


def check_stock_presence(path: Path, code: str, lot: str) -> bool:
    try:
        import pandas as pd
    except ImportError:
        return False
    workbook = pd.read_excel(path, sheet_name=None, dtype=str)
    for sheet in workbook.values():
        normalized_columns = {normalize_key(column): column for column in sheet.columns}
        code_column = first_existing(normalized_columns, ["cod_articol", "cod", "cod_produs"])
        lot_column = first_existing(normalized_columns, ["lot", "nr_lot", "numar_lot"])
        if not code_column or not lot_column:
            continue
        matches = sheet[(sheet[code_column].astype(str).str.strip() == code) & (sheet[lot_column].astype(str).str.strip() == lot)]
        if not matches.empty:
            return True
    return False


def first_existing(mapping: dict[str, str], keys: Iterable[str]) -> str | None:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def is_food_raw_material(code: str, name: str) -> bool:
    text = f"{code} {name}".casefold()
    return code.startswith("DS") or "pastrav" in text or "păstrăv" in text


def is_auxiliary(code: str, name: str) -> bool:
    text = f"{code} {name}".casefold()
    return "alisol" in text or "gaz" in text


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def parse_decimal(value: object) -> Decimal | None:
    text = clean(value).replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        return None
    try:
        return Decimal(text.replace(",", "."))
    except InvalidOperation:
        return None


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def normalize_key(value: object) -> str:
    text = str(value).strip().casefold()
    replacements = str.maketrans({"ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t"})
    text = text.translate(replacements)
    return "_".join(part for part in text.replace(".", " ").replace("-", " ").split() if part)


def reference_to_jsonable(result: ReferenceResult) -> dict[str, object]:
    payload = asdict(result)
    return payload


def reference_to_markdown(result: ReferenceResult) -> str:
    lines: list[str] = []
    lines.append(f"# Reference traceability extraction")
    lines.append("")
    lines.append(f"Cod: `{result.code}`")
    lines.append(f"Lot: `{result.lot}`")
    lines.append(f"Source directory: `{result.source_directory}`")
    lines.append("")
    lines.append("## Source row counts")
    lines.append(f"- WMS rows for code+lot: {result.wms_rows}")
    lines.append(f"- PRD rows for PRE code+lot: {result.prd_rows}")
    lines.append(f"- Stock contains code+lot: {result.stock_found}")
    append_table(lines, "## WMS operation totals", result.wms_operation_totals)
    append_table(lines, "## WMS delivery totals", result.wms_delivery_totals)
    append_table(lines, "## WMS production-out totals", result.wms_production_out_totals)
    append_table(lines, "## PRD production by unique order", result.prd_production_totals)
    append_table(lines, "## PRD food raw materials", result.prd_raw_materials)
    append_table(lines, "## PRD packaging", result.prd_packaging)
    append_table(lines, "## PRD auxiliaries / gas", result.prd_auxiliaries)
    if result.notes:
        lines.append("## Notes")
        for note in result.notes:
            lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def append_table(lines: list[str], title: str, rows: list[dict[str, str]]) -> None:
    lines.append("")
    lines.append(title)
    if not rows:
        lines.append("")
        lines.append("No rows.")
        return
    columns = list(rows[0].keys())
    lines.append("")
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")


if __name__ == "__main__":
    raise SystemExit(main())
