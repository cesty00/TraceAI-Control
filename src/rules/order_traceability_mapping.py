"""Production-order traceability mapping.

Builds a report table that connects, per production order:
- finished goods quantity from PRD PRE_*
- WMS production-out and finished-goods delivery evidence
- PRD CON_* consumptions by category
- WMS third-party deliveries for consumed raw-material lots, when any exist
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

PACKAGING_TERMS = (
    "ambalaj", "ambalaje", "etichete", "eticheta", "etichetă", "folie", "film",
    "cutie", "caserole", "capac", "punga", "pungă", "carton", "pad", "absorbante",
)
RAW_MATERIAL_TERMS = (
    "materie prima", "materie primă", "materii prime", "ingredient", "refrigerat-p",
    "peste", "pește", "file", "creveti", "creveți", "pastrav", "păstrăv", "somon",
    "dorada", "ton", "calamar", "scoici",
)
AUXILIARY_TERMS = ("alisol", "gaz")
CATEGORY_LABELS = {
    "raw_material": "Materie primă alimentară",
    "packaging": "Ambalaj",
    "auxiliary": "Auxiliar / gaz",
}


@dataclass(frozen=True)
class ReportRowPayload:
    values: dict[str, str]
    source_key: str | None
    source_name: str | None
    sheet_name: str | None
    row_number: int | None


@dataclass(frozen=True)
class SourceRow:
    source_key: str
    source_name: str
    sheet_name: str | None
    row_number: int
    values: dict[str, str]
    original_values: dict[str, str]


def build_order_traceability_rows(result: Any) -> list[ReportRowPayload]:
    dataset = result.core.normalized_dataset
    product_code = str(result.core.selection.input_code).strip()
    product_lot = str(result.core.selection.input_lot).strip()
    nomenclator = build_nomenclator_index(dataset)
    prd_rows = matching_prd_rows(dataset, product_code, product_lot)
    if not prd_rows:
        return []

    wms_rows = list_wms_rows(dataset)
    production_by_order = build_production_by_order(prd_rows)
    component_rows = build_components_by_order(prd_rows, nomenclator)
    production_out_by_order = build_wms_production_out_by_order(wms_rows, product_code, product_lot)
    finished_delivery_by_order = assign_finished_deliveries(production_by_order, wms_rows, product_code, product_lot)
    raw_third_party = build_raw_material_third_party_delivery_index(wms_rows, component_rows)

    rows: list[ReportRowPayload] = []
    for order in sorted(production_by_order):
        production = production_by_order[order]
        components = component_rows.get(order, [])
        if not components:
            rows.append(build_payload(order, production, production_out_by_order, finished_delivery_by_order, None, "", production["record"]))
            continue
        for component in sorted(components, key=lambda item: (item["category"], item["code"], item["lot"])):
            delivery_summary = raw_third_party.get((component["code"], component["lot"]), "NU") if component["category"] == "raw_material" else "Nu se aplică"
            rows.append(build_payload(order, production, production_out_by_order, finished_delivery_by_order, component, delivery_summary, component["record"]))
    return rows


def build_payload(
    order: str,
    production: dict[str, Any],
    production_out_by_order: dict[str, str],
    finished_delivery_by_order: dict[str, str],
    component: dict[str, Any] | None,
    third_party_summary: str,
    record: SourceRow,
) -> ReportRowPayload:
    values = {
        "Comandă producție": order,
        "Produs finit": production["name"],
        "Cantitate produs finit": production["quantity"],
        "UM produs finit": production["unit"],
        "WMS production-out": production_out_by_order.get(order, "FARA DATE IDENTIFICATE"),
        "Livrare produs finit asociată": finished_delivery_by_order.get(order, "FARA DATE IDENTIFICATE"),
        "Categorie consum": CATEGORY_LABELS.get(component["category"], component["category"]) if component else "FARA DATE IDENTIFICATE",
        "Cod consum": component["code"] if component else "FARA DATE IDENTIFICATE",
        "Lot consum": component["lot"] if component else "FARA DATE IDENTIFICATE",
        "Denumire consum": component["name"] if component else "FARA DATE IDENTIFICATE",
        "Cantitate consum": component["quantity"] if component else "FARA DATE IDENTIFICATE",
        "UM consum": component["unit"] if component else "FARA DATE IDENTIFICATE",
        "Livrări consum către terți": third_party_summary or "NU",
    }
    return ReportRowPayload(values, record.source_key, record.source_name, record.sheet_name, record.row_number)


def matching_prd_rows(dataset: Any, product_code: str, product_lot: str) -> list[SourceRow]:
    rows: list[SourceRow] = []
    for table in getattr(dataset, "tables", []):
        if table.source_key != "production":
            continue
        for row in table.rows:
            values = dict(row.values)
            original_values = dict(getattr(row, "original_values", {}) or {})
            merged = dict(values)
            merged.update(original_values)
            if normalize_match_value(value_by_alias(merged, "pre_cod_articol", "PRE_Cod Articol")) != normalize_match_value(product_code):
                continue
            if normalize_match_value(value_by_alias(merged, "pre_lot", "PRE_LOT")) != normalize_match_value(product_lot):
                continue
            rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, values, original_values))
    return rows


def list_wms_rows(dataset: Any) -> list[SourceRow]:
    rows: list[SourceRow] = []
    for table in getattr(dataset, "tables", []):
        if table.source_key != "wms":
            continue
        for row in table.rows:
            rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, dict(row.values), dict(getattr(row, "original_values", {}) or {})))
    return rows


def build_production_by_order(prd_rows: list[SourceRow]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in prd_rows:
        values = merged_values(row)
        order = value_by_alias(values, "numar_comanda", "Numar Comanda")
        if not order:
            continue
        result.setdefault(
            order,
            {
                "code": value_by_alias(values, "pre_cod_articol", "PRE_Cod Articol"),
                "lot": value_by_alias(values, "pre_lot", "PRE_LOT"),
                "name": value_by_alias(values, "pre_denumire_articol", "PRE_Denumire Articol"),
                "quantity": value_by_alias(values, "pre_cantitate_predare", "PRE_Cantitate Predare"),
                "unit": value_by_alias(values, "pre_u_m", "PRE_U.M."),
                "record": row,
            },
        )
    return result


def build_components_by_order(prd_rows: list[SourceRow], nomenclator: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for row in prd_rows:
        values = merged_values(row)
        order = value_by_alias(values, "numar_comanda", "Numar Comanda")
        code = value_by_alias(values, "con_cod_articol", "CON_Cod Articol")
        lot = value_by_alias(values, "con_lot", "CON_LOT")
        name = value_by_alias(values, "con_denumire_articol", "CON_Denumire Articol")
        unit = value_by_alias(values, "con_u_m", "CON_U.M.")
        quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata", "CON_Cantitate Consumata"))
        if not order or not code or not lot or quantity is None:
            continue
        category = classify_component(code, name, nomenclator.get(code, ""))
        key = (order, category, code, lot, name, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": row})
        bucket["quantity"] += quantity

    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (order, category, code, lot, name, unit), bucket in buckets.items():
        result[order].append(
            {
                "category": category,
                "code": code,
                "lot": lot,
                "name": name,
                "quantity": format_decimal(bucket["quantity"]),
                "unit": unit,
                "record": bucket["record"],
            }
        )
    return result


def build_wms_production_out_by_order(wms_rows: list[SourceRow], product_code: str, product_lot: str) -> dict[str, str]:
    buckets: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for row in wms_rows:
        values = merged_values(row)
        if not same_article_lot(values, product_code, product_lot):
            continue
        operation = value_by_alias(values, "tip_operatiune", "Tip operatiune")
        reason = value_by_alias(values, "cod_motiv", "Cod-motiv")
        if operation.casefold() != "ajustare pozitiva" or reason.casefold() != "production-out":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda", "Numar comanda")
        unit = value_by_alias(values, "um", "UM")
        buckets[(order, unit)] += quantity
    return {order: f"{format_decimal(total)} {unit}" for (order, unit), total in sorted(buckets.items()) if order}


def assign_finished_deliveries(production_by_order: dict[str, dict[str, Any]], wms_rows: list[SourceRow], product_code: str, product_lot: str) -> dict[str, str]:
    deliveries_by_quantity: dict[tuple[str, str], deque[str]] = defaultdict(deque)
    delivery_totals: dict[tuple[str, str, str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for row in wms_rows:
        values = merged_values(row)
        if not same_article_lot(values, product_code, product_lot):
            continue
        if value_by_alias(values, "tip_operatiune", "Tip operatiune").casefold() != "livrare":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        key = (
            value_by_alias(values, "numar_comanda", "Numar comanda"),
            value_by_alias(values, "document_comanda", "Document comanda"),
            value_by_alias(values, "partener", "Partener"),
            value_by_alias(values, "um", "UM"),
        )
        delivery_totals[key] += quantity
    for (order, document, client, unit), quantity in sorted(delivery_totals.items()):
        deliveries_by_quantity[(format_decimal(abs(quantity)), unit)].append(f"{order} / {document} / {client} / {format_decimal(quantity)} {unit}")

    assignments: dict[str, str] = {}
    for order in sorted(production_by_order):
        production = production_by_order[order]
        key = (format_decimal(parse_decimal(production["quantity"]) or Decimal("0")), production["unit"])
        if deliveries_by_quantity[key]:
            assignments[order] = deliveries_by_quantity[key].popleft()
    return assignments


def build_raw_material_third_party_delivery_index(wms_rows: list[SourceRow], component_rows: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], str]:
    raw_keys = {(component["code"], component["lot"]) for components in component_rows.values() for component in components if component["category"] == "raw_material"}
    totals: dict[tuple[str, str], dict[tuple[str, str, str], Decimal]] = {key: defaultdict(lambda: Decimal("0")) for key in raw_keys}
    for row in wms_rows:
        values = merged_values(row)
        code = value_by_alias(values, "cod_articol", "Cod articol")
        lot = value_by_alias(values, "lot", "Lot")
        key = (code, lot)
        if key not in totals:
            continue
        if value_by_alias(values, "tip_operatiune", "Tip operatiune").casefold() != "livrare":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        delivery_key = (
            value_by_alias(values, "numar_comanda", "Numar comanda"),
            value_by_alias(values, "document_comanda", "Document comanda"),
            value_by_alias(values, "partener", "Partener"),
        )
        totals[key][delivery_key] += quantity

    result: dict[tuple[str, str], str] = {}
    for key, deliveries in totals.items():
        if not deliveries:
            result[key] = "NU"
            continue
        total_quantity = sum(deliveries.values(), Decimal("0"))
        examples = [f"{order}/{document}/{client}: {format_decimal(quantity)}" for (order, document, client), quantity in sorted(deliveries.items())[:3]]
        suffix = "" if len(deliveries) <= 3 else f"; +{len(deliveries) - 3} alte livrări"
        result[key] = f"DA; total {format_decimal(total_quantity)}; " + "; ".join(examples) + suffix
    return result


def same_article_lot(values: dict[str, str], code: str, lot: str) -> bool:
    return normalize_match_value(value_by_alias(values, "cod_articol", "Cod articol")) == normalize_match_value(code) and normalize_match_value(value_by_alias(values, "lot", "Lot")) == normalize_match_value(lot)


def build_nomenclator_index(dataset: Any) -> dict[str, str]:
    items: dict[str, str] = {}
    for table in getattr(dataset, "tables", []):
        if table.source_key != "nomenclator":
            continue
        for row in table.rows:
            values = dict(row.values)
            values.update(getattr(row, "original_values", {}) or {})
            code = value_by_alias(values, "cod", "cod_articol", "cod_produs", "Cod", "Cod articol")
            if not code:
                code = row.code_lot_hints.get("code", "")
            if code:
                items.setdefault(code, " ".join(str(value) for value in values.values() if str(value).strip()))
    return items


def classify_component(code: str, prd_name: str, nomenclator_text: str) -> str:
    text = normalize_text(f"{code} {prd_name} {nomenclator_text}")
    if any(term in text for term in AUXILIARY_TERMS) or code == "60001":
        return "auxiliary"
    if any(normalize_text(term) in text for term in PACKAGING_TERMS) or code.startswith(("1", "2", "4", "5")):
        return "packaging"
    if any(normalize_text(term) in text for term in RAW_MATERIAL_TERMS) or code.startswith("DS"):
        return "raw_material"
    return "packaging"


def merged_values(record: Any) -> dict[str, str]:
    values = dict(getattr(record, "values", {}) or {})
    for key, value in (getattr(record, "original_values", {}) or {}).items():
        values.setdefault(key, value)
    return values


def value_by_alias(values: dict[str, str], *aliases: str) -> str:
    normalized_aliases = {normalize_key(alias) for alias in aliases}
    for key, value in values.items():
        if normalize_key(key) in normalized_aliases:
            return str(value).strip()
    return ""


def normalize_match_value(value: object) -> str:
    return " ".join(str(value).strip().casefold().split())


def normalize_key(value: object) -> str:
    text = remove_diacritics(str(value)).casefold().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def normalize_text(value: object) -> str:
    return remove_diacritics(str(value)).casefold()


def remove_diacritics(value: str) -> str:
    return value.translate(str.maketrans({"ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t", "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ş": "S", "Ț": "T", "Ţ": "T"}))


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
