"""Independent reference extractor for TraceAI source files.

Reads raw operational files and produces a human-checkable reference report for
one code + lot. It is intentionally separate from the app pipeline so expected
results can be verified before business mapping is coded.
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
class NomenclatorItem:
    code: str
    name: str = ""
    classifier_text: str = ""
    source_sheet: str = ""


@dataclass
class ReferenceResult:
    code: str
    lot: str
    source_directory: str
    wms_rows: int = 0
    prd_rows: int = 0
    nomenclator_items: int = 0
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
    nomenclator_path = source_dir / "nomenclator.xlsx"
    stock_path = source_dir / "stoc la moment original.xlsx"

    nomenclator = load_nomenclator(nomenclator_path, result) if nomenclator_path.exists() else {}
    result.nomenclator_items = len(nomenclator)
    if not nomenclator_path.exists():
        result.notes.append("Nomenclator source missing: nomenclator.xlsx")

    if wms_path.exists():
        extract_wms_reference(wms_path, result)
    else:
        result.notes.append("WMS source missing: trasabilitate_wms.csv")

    if prd_path.exists():
        extract_prd_reference(prd_path, result, nomenclator)
    else:
        result.notes.append("PRD source missing: rapoarte productie.csv")

    if stock_path.exists():
        result.stock_found = check_stock_presence(stock_path, code, lot)
    else:
        result.stock_found = None
        result.notes.append("Stock source missing: stoc la moment original.xlsx")

    return result


def load_nomenclator(path: Path, result: ReferenceResult) -> dict[str, NomenclatorItem]:
    try:
        import pandas as pd
    except ImportError:
        result.notes.append("pandas missing; nomenclator classification unavailable")
        return {}

    items: dict[str, NomenclatorItem] = {}
    try:
        workbook = pd.read_excel(path, sheet_name=None, dtype=str)
    except Exception as exc:  # pragma: no cover - diagnostic path
        result.notes.append(f"Could not read nomenclator.xlsx: {exc}")
        return {}

    for sheet_name, sheet in workbook.items():
        normalized = {normalize_key(column): column for column in sheet.columns}
        code_col = first_existing(normalized, ["cod_articol", "cod", "cod_produs", "cod_item", "article_code", "item_code"])
        if not code_col:
            continue
        name_col = first_existing(normalized, ["denumire_articol", "denumire", "nume", "descriere", "produs", "articol"])
        classifier_cols = [
            original
            for norm, original in normalized.items()
            if any(token in norm for token in ("categorie", "grupa", "grup", "tip", "clasa", "familie", "subfamilie", "brand", "denumire"))
        ]
        for _, row in sheet.iterrows():
            code = clean(row.get(code_col))
            if not code or code.casefold() == "nan":
                continue
            name = clean(row.get(name_col)) if name_col else ""
            classifier_parts = [clean(row.get(column)) for column in classifier_cols]
            classifier_text = " ".join(part for part in classifier_parts if part and part.casefold() != "nan")
            items.setdefault(code, NomenclatorItem(code=code, name=name, classifier_text=classifier_text, source_sheet=sheet_name))
    return items


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
        operation_totals.setdefault((operation, reason, unit), QuantityTotal(unit)).add(quantity)
        if operation.casefold() == "livrare":
            key = (clean(row.get("Numar comanda")), clean(row.get("Document comanda")), clean(row.get("Partener")), unit)
            delivery_totals.setdefault(key, QuantityTotal(unit)).add(quantity)
        if operation.casefold() == "ajustare pozitiva" and reason.casefold() == "production-out":
            order = clean(row.get("Numar comanda")) or clean(row.get("Document intrare")) or clean(row.get("Document comanda"))
            production_totals.setdefault((order, unit), QuantityTotal(unit)).add(quantity)

    result.wms_operation_totals = [
        {"tip_operatiune": operation, "cod_motiv": reason, "um": total.unit, "total": format_decimal(total.total), "rows": str(total.rows)}
        for (operation, reason, _unit), total in sorted(operation_totals.items())
    ]
    result.wms_delivery_totals = [
        {"numar_comanda": order, "document_comanda": document, "client": partner, "um": total.unit, "total": format_decimal(total.total), "rows": str(total.rows)}
        for (order, document, partner, _unit), total in sorted(delivery_totals.items())
    ]
    result.wms_production_out_totals = [
        {"comanda": order, "um": total.unit, "total": format_decimal(total.total), "rows": str(total.rows)}
        for (order, _unit), total in sorted(production_totals.items())
    ]


def extract_prd_reference(path: Path, result: ReferenceResult, nomenclator: dict[str, NomenclatorItem]) -> None:
    rows = [
        row
        for row in read_csv_dicts(path)
        if clean(row.get("PRE_Cod Articol")) == result.code and lot_matches_target(clean(row.get("PRE_LOT")), result.lot)
    ]
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
        component_key = (clean(row.get("CON_Cod Articol")), clean(row.get("CON_LOT")), clean(row.get("CON_Denumire Articol")), clean(row.get("CON_U.M.")))
        if not component_key[0]:
            continue
        bucket = components.setdefault(component_key, {"rows": 0, "consumed": Decimal("0"), "orders": set(), "control_by_order": defaultdict(Decimal)})
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

    for (component_code, component_lot, prd_name, unit), bucket in components.items():
        nom_item = nomenclator.get(component_code)
        display_name = nom_item.name if nom_item and nom_item.name else prd_name
        item = {
            "cod": component_code,
            "lot": component_lot,
            "denumire": display_name,
            "denumire_prd": prd_name,
            "clasificare_nomenclator": nom_item.classifier_text if nom_item else "FARA NOMENCLATOR",
            "cantitate_consumata": format_decimal(bucket["consumed"]),
            "um": unit,
            "greutate_control_deduplicata": format_decimal(sum(bucket["control_by_order"].values(), Decimal("0"))),
            "comenzi": ", ".join(sorted(bucket["orders"])),
            "rows": str(bucket["rows"]),
        }
        category = classify_component(component_code, prd_name, nom_item)
        if category == "auxiliary":
            auxiliaries.append(item)
        elif category == "raw_material":
            raw_materials.append(item)
        else:
            packaging.append(item)

    result.prd_raw_materials = sorted(raw_materials, key=lambda item: (item["cod"], item["lot"]))
    result.prd_packaging = sorted(packaging, key=lambda item: (item["cod"], item["lot"]))
    result.prd_auxiliaries = sorted(auxiliaries, key=lambda item: (item["cod"], item["lot"]))


def classify_component(code: str, prd_name: str, nom_item: NomenclatorItem | None) -> str:
    text = f"{code} {prd_name}"
    if nom_item:
        text = f"{text} {nom_item.name} {nom_item.classifier_text}"
    folded = text.casefold()
    if any(term in folded for term in ("alisol", "gaz")):
        return "auxiliary"
    if any(term in folded for term in ("ambalaj", "ambalaje", "etichete", "eticheta", "etichetă", "folie", "film", "cutie", "caserole", "capac", "punga", "pungă", "carton")):
        return "packaging"
    if nom_item and any(term in folded for term in ("materie prima", "materie primă", "materii prime", "ingredient", "peste", "pește", "refrigerat-p")):
        return "raw_material"
    if code.startswith("DS"):
        return "raw_material"
    if code.startswith(("1", "2", "4", "5")):
        return "packaging"
    return "packaging"


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


def lot_matches_target(candidate_lot: str, target_lot: str) -> bool:
    if not candidate_lot or not target_lot:
        return False
    if candidate_lot == target_lot:
        return True
    return target_lot in extract_lot_tokens(candidate_lot)


def extract_lot_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for part in value.split(","):
        token = clean(part)
        if not token:
            continue
        quantity_marker = token.casefold().find("(cant:")
        if quantity_marker != -1:
            token = token[:quantity_marker].strip()
        if token:
            tokens.append(token)
    return tokens


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def parse_decimal(value: object) -> Decimal | None:
    text = clean(value).replace(" ", "")
    if not text or ("," in text and "." in text):
        return None
    try:
        return Decimal(text.replace(",", "."))
    except InvalidOperation:
        return None


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() == "nan" else text


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def normalize_key(value: object) -> str:
    text = str(value).strip().casefold()
    text = text.translate(str.maketrans({"ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t"}))
    return "_".join(part for part in text.replace(".", " ").replace("-", " ").replace("/", " ").split() if part)


def reference_to_jsonable(result: ReferenceResult) -> dict[str, object]:
    return asdict(result)


def reference_to_markdown(result: ReferenceResult) -> str:
    lines: list[str] = []
    lines.append("# Reference traceability extraction")
    lines.append("")
    lines.append(f"Cod: `{result.code}`")
    lines.append(f"Lot: `{result.lot}`")
    lines.append(f"Source directory: `{result.source_directory}`")
    lines.append("")
    lines.append("## Source row counts")
    lines.append(f"- WMS rows for code+lot: {result.wms_rows}")
    lines.append(f"- PRD rows for PRE code+lot: {result.prd_rows}")
    lines.append(f"- Nomenclator items loaded: {result.nomenclator_items}")
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
