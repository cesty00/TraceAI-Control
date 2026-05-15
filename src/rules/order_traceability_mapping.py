"""Production-order traceability mapping.

Builds a report table that connects, per production order:
- finished goods quantity from PRD PRE_*
- WMS production-out and finished-goods delivery evidence
- PRD CON_* consumptions by category
- WMS third-party deliveries for consumed raw-material lots, when any exist
- WMS receipt and stock summaries for consumed component lots, when available

DATA-GAP-01: date-like fields are propagated as presentation-neutral values so
AuditTraceabilityReport/DOCX can show them when the source files contain them.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from src.rules.pre_lot_classification import pre_lot_matches_input as shared_pre_lot_matches_input

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
MISSING = "FARA DATE IDENTIFICATE"
DATE_ALIASES = (
    "data", "dată", "date",
    "data_operatiune", "data_operațiune", "data_miscare", "data_mișcare",
    "data_operare", "data_inregistrare", "data_înregistrare",
    "data_document", "data_doc", "data_livrare", "data_receptie", "data_recepție",
    "data_productie", "data_producție", "data_fabricatie", "data_fabricație",
    "created_at", "document_date", "delivery_date", "receipt_date", "production_date",
    "Data", "Dată", "Data document", "Dată document", "Data livrare", "Dată livrare",
    "Data receptie", "Data recepție", "Dată recepție", "Data producției", "Data productie",
)


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
    code_lot_hints: dict[str, str] = field(default_factory=dict)


def build_order_traceability_rows(result: Any) -> list[ReportRowPayload]:
    dataset = result.core.normalized_dataset
    product_code = str(result.core.selection.input_code).strip()
    product_lot = str(result.core.selection.input_lot).strip()
    nomenclator = build_nomenclator_index(dataset)
    prd_rows = matching_prd_rows(dataset, product_code, product_lot)
    if not prd_rows:
        return []

    wms_rows = list_source_rows(dataset, "wms")
    stock_rows = list_source_rows(dataset, "stock")
    production_by_order = build_production_by_order(prd_rows)
    component_rows = build_components_by_order(prd_rows, nomenclator)
    production_out_by_order = build_wms_production_out_by_order(wms_rows, product_code, product_lot)
    production_dates_by_order = build_wms_production_out_dates_by_order(wms_rows, product_code, product_lot)
    fill_missing_production_dates(production_by_order, production_dates_by_order)
    finished_delivery_by_order = assign_finished_deliveries(production_by_order, wms_rows, product_code, product_lot)
    raw_third_party = build_raw_material_third_party_delivery_index(wms_rows, component_rows)
    component_receipts = build_component_receipt_index(wms_rows, component_rows)
    structured_component_receipts = build_component_structured_receipt_index(wms_rows, component_rows)
    component_stock = build_component_stock_index(stock_rows, component_rows)

    rows: list[ReportRowPayload] = []
    for order in sorted(production_by_order):
        production = production_by_order[order]
        components = component_rows.get(order, [])
        if not components:
            rows.append(
                build_payload(
                    order,
                    production,
                    production_out_by_order,
                    finished_delivery_by_order,
                    None,
                    "",
                    MISSING,
                    MISSING,
                    production["record"],
                )
            )
            continue
        for component in sorted(components, key=lambda item: (item["category"], item["code"], item["lot"])):
            component_key = (component["code"], component["lot"])
            delivery_summary = raw_third_party.get(component_key, "NU") if component["category"] == "raw_material" else "Nu se aplică"
            rows.append(
                build_payload(
                    order,
                    production,
                    production_out_by_order,
                    finished_delivery_by_order,
                    component,
                    delivery_summary,
                    component_receipts.get(component_key, MISSING),
                    structured_component_receipts.get(component_key),
                    component_stock.get(component_key, MISSING),
                    component["record"],
                )
            )
    return rows


def build_payload(
    order: str,
    production: dict[str, Any],
    production_out_by_order: dict[str, str],
    finished_delivery_by_order: dict[str, str],
    component: dict[str, Any] | None,
    third_party_summary: str,
    receipt_summary: str,
    structured_receipt: dict[str, str] | None,
    stock_summary: str,
    record: SourceRow,
) -> ReportRowPayload:
    receipt_fields = structured_receipt or empty_structured_receipt_fields()
    values = {
        "Comandă producție": order,
        "Produs finit": production["name"],
        "Cantitate produs finit": production["quantity"],
        "UM produs finit": production["unit"],
        "Data producției": production.get("production_date", MISSING),
        "WMS production-out": production_out_by_order.get(order, MISSING),
        "Livrare produs finit asociată": finished_delivery_by_order.get(order, MISSING),
        "Categorie consum": CATEGORY_LABELS.get(component["category"], component["category"]) if component else MISSING,
        "Cod consum": component["code"] if component else MISSING,
        "Lot consum": component["lot"] if component else MISSING,
        "Denumire consum": component["name"] if component else MISSING,
        "Cantitate consum": component["quantity"] if component else MISSING,
        "UM consum": component["unit"] if component else MISSING,
        "Livrări consum către terți": third_party_summary or "NU",
        "Recepții WMS consum": receipt_summary or MISSING,
        "Cantitate recepționată consum": receipt_fields["received_quantity"],
        "Data recepție consum": receipt_fields["receipt_date"],
        "Furnizor recepție consum": receipt_fields["supplier"],
        "Stoc consum la moment": stock_summary or MISSING,
    }
    return ReportRowPayload(values, record.source_key, record.source_name, record.sheet_name, record.row_number)


def matching_prd_rows(dataset: Any, product_code: str, product_lot: str) -> list[SourceRow]:
    rows: list[SourceRow] = []
    normalized_code = normalize_match_value(product_code)
    for table in getattr(dataset, "tables", []):
        if table.source_key != "production":
            continue
        for row in table.rows:
            values = dict(row.values)
            original_values = dict(getattr(row, "original_values", {}) or {})
            merged = dict(values)
            merged.update(original_values)
            if normalize_match_value(value_by_alias(merged, "pre_cod_articol", "PRE_Cod Articol")) != normalized_code:
                continue
            if not pre_lot_matches_input(value_by_alias(merged, "pre_lot", "PRE_LOT"), product_lot):
                continue
            rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, values, original_values, dict(getattr(row, "code_lot_hints", {}) or {})))
    return rows


def list_source_rows(dataset: Any, source_key: str) -> list[SourceRow]:
    rows: list[SourceRow] = []
    for table in getattr(dataset, "tables", []):
        if table.source_key != source_key:
            continue
        for row in table.rows:
            rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, dict(row.values), dict(getattr(row, "original_values", {}) or {}), dict(getattr(row, "code_lot_hints", {}) or {})))
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
                "production_date": first_non_empty(value_by_alias(values, "data_productie", "data_producție", "Data producției", "Data productie"), value_by_alias(values, *DATE_ALIASES), MISSING),
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


def component_keys(component_rows: dict[str, list[dict[str, Any]]]) -> set[tuple[str, str]]:
    return {(component["code"], component["lot"]) for components in component_rows.values() for component in components}


def normalized_component_key(code: object, lot: object) -> tuple[str, str]:
    return normalize_match_value(code), normalize_match_value(lot)


def component_key_lookup(component_rows: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], tuple[str, str]]:
    return {normalized_component_key(code, lot): (code, lot) for code, lot in component_keys(component_rows)}


def build_wms_production_out_by_order(wms_rows: list[SourceRow], product_code: str, product_lot: str) -> dict[str, str]:
    buckets: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for row in wms_rows:
        values = merged_values(row)
        if not is_wms_production_out_row(values, product_code, product_lot):
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda", "Numar comanda")
        unit = value_by_alias(values, "um", "UM")
        buckets[(order, unit)] += quantity
    return {order: f"{format_decimal(total)} {unit}" for (order, unit), total in sorted(buckets.items()) if order}


def build_wms_production_out_dates_by_order(wms_rows: list[SourceRow], product_code: str, product_lot: str) -> dict[str, str]:
    dates_by_order: dict[str, list[str]] = defaultdict(list)
    for row in wms_rows:
        values = merged_values(row)
        if not is_wms_production_out_row(values, product_code, product_lot):
            continue
        order = value_by_alias(values, "numar_comanda", "Numar comanda")
        production_date = value_by_alias(values, *DATE_ALIASES)
        if order and production_date and production_date not in dates_by_order[order]:
            dates_by_order[order].append(production_date)
    return {order: "; ".join(dates) for order, dates in sorted(dates_by_order.items())}


def fill_missing_production_dates(production_by_order: dict[str, dict[str, Any]], dates_by_order: dict[str, str]) -> None:
    for order, production in production_by_order.items():
        current_date = str(production.get("production_date", "")).strip()
        if current_date and current_date != MISSING:
            continue
        fallback_date = dates_by_order.get(order, "")
        if fallback_date:
            production["production_date"] = fallback_date


def is_wms_production_out_row(values: dict[str, str], product_code: str, product_lot: str) -> bool:
    if not same_article_lot(values, product_code, product_lot):
        return False
    operation = value_by_alias(values, "tip_operatiune", "Tip operatiune")
    reason = value_by_alias(values, "cod_motiv", "Cod-motiv")
    return operation.casefold() == "ajustare pozitiva" and reason.casefold() == "production-out"


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


def build_component_receipt_index(wms_rows: list[SourceRow], component_rows: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], str]:
    keys = component_keys(component_rows)
    totals: dict[tuple[str, str], dict[tuple[str, str, str, str, str], Decimal]] = {key: defaultdict(lambda: Decimal("0")) for key in keys}
    for row in wms_rows:
        values = merged_values(row)
        key = (value_by_alias(values, "cod_articol", "Cod articol"), value_by_alias(values, "lot", "Lot"))
        if key not in totals:
            continue
        if value_by_alias(values, "tip_operatiune", "Tip operatiune").casefold() != "receptie":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        receipt_key = (
            value_by_alias(values, "document_intrare", "Document intrare"),
            value_by_alias(values, "document_comanda", "Document comanda"),
            value_by_alias(values, "partener", "Partener"),
            value_by_alias(values, "um", "UM"),
            first_non_empty(value_by_alias(values, *DATE_ALIASES), MISSING),
        )
        totals[key][receipt_key] += quantity

    result: dict[tuple[str, str], str] = {}
    for key, receipts in totals.items():
        if not receipts:
            continue
        unit_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for (_document_in, _document_order, _supplier, unit, _date), quantity in receipts.items():
            unit_totals[unit] += quantity
        totals_text = ", ".join(f"{format_decimal(quantity)} {unit}" for unit, quantity in sorted(unit_totals.items()))
        examples = [
            format_receipt_example(document_in, document_order, supplier, quantity, unit, receipt_date)
            for (document_in, document_order, supplier, unit, receipt_date), quantity in sorted(receipts.items())[:3]
        ]
        suffix = "" if len(receipts) <= 3 else f"; +{len(receipts) - 3} alte recepții"
        result[key] = f"total {totals_text}; " + "; ".join(examples) + suffix
    return result


def build_component_structured_receipt_index(wms_rows: list[SourceRow], component_rows: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], dict[str, str]]:
    keys = component_keys(component_rows)
    receipt_dates: dict[tuple[str, str], set[str]] = defaultdict(set)
    suppliers: dict[tuple[str, str], set[str]] = defaultdict(set)
    quantity_totals: dict[tuple[str, str], dict[str, Decimal]] = {key: defaultdict(lambda: Decimal("0")) for key in keys}
    for row in wms_rows:
        values = merged_values(row)
        key = (value_by_alias(values, "cod_articol", "Cod articol"), value_by_alias(values, "lot", "Lot"))
        if key not in quantity_totals:
            continue
        if value_by_alias(values, "tip_operatiune", "Tip operatiune").casefold() != "receptie":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        unit = value_by_alias(values, "um", "UM")
        if quantity is not None and unit:
            quantity_totals[key][unit] += quantity
        supplier = value_by_alias(values, "partener", "Partener")
        if supplier:
            suppliers[key].add(supplier)
        receipt_date = first_non_empty(value_by_alias(values, *DATE_ALIASES), MISSING)
        if receipt_date != MISSING:
            receipt_dates[key].add(receipt_date)

    result: dict[tuple[str, str], dict[str, str]] = {}
    for key in keys:
        if not quantity_totals[key] and not suppliers[key] and not receipt_dates[key]:
            continue
        received_quantity = "; ".join(
            f"{format_decimal(quantity)} {unit}" for unit, quantity in sorted(quantity_totals[key].items())
        ) or MISSING
        result[key] = {
            "received_quantity": received_quantity,
            "receipt_date": "; ".join(sorted(receipt_dates[key])) or MISSING,
            "supplier": "; ".join(sorted(suppliers[key])) or MISSING,
        }
    return result


def empty_structured_receipt_fields() -> dict[str, str]:
    return {
        "received_quantity": MISSING,
        "receipt_date": MISSING,
        "supplier": MISSING,
    }


def format_receipt_example(document_in: str, document_order: str, supplier: str, quantity: Decimal, unit: str, receipt_date: str = MISSING) -> str:
    reference = document_in or document_order or "fără document"
    supplier_text = supplier or "fără furnizor"
    date_suffix = "" if not receipt_date or receipt_date == MISSING else f"/{receipt_date}"
    return f"{reference}/{supplier_text}{date_suffix}: {format_decimal(quantity)} {unit}"


def build_component_stock_index(stock_rows: list[SourceRow], component_rows: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], str]:
    lookup = component_key_lookup(component_rows)
    totals: dict[tuple[str, str], dict[tuple[str, str], Decimal]] = {key: defaultdict(lambda: Decimal("0")) for key in component_keys(component_rows)}
    locations: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in stock_rows:
        values = merged_values(row)
        code = first_non_empty(
            value_by_alias(values, "cod_articol", "cod", "cod_produs", "articol_cod", "item_code", "sku", "Cod articol", "Cod"),
            row.code_lot_hints.get("code", ""),
        )
        lot = first_non_empty(
            value_by_alias(values, "lot", "lot_articol", "lot_produs", "batch", "batch_no", "Lot"),
            row.code_lot_hints.get("lot", ""),
        )
        key = lookup.get(normalized_component_key(code, lot))
        if key is None:
            continue
        quantity = parse_decimal(
            value_by_alias(
                values,
                "stoc", "stoc_la_moment", "stoc_disponibil", "cantitate_stoc", "cantitate", "cantitate_disponibila",
                "sold", "sold_final", "qty", "quantity", "Stoc", "Cantitate",
            )
        )
        if quantity is None:
            continue
        unit = first_non_empty(value_by_alias(values, "um", "u_m", "unitate_masura", "unit", "UM", "U.M."), "")
        location = value_by_alias(values, "locatie", "locație", "depozit", "gestiune", "magazie", "warehouse", "location", "Locație")
        totals[key][(unit, location)] += quantity
        if location:
            locations[key].add(location)

    result: dict[tuple[str, str], str] = {}
    for key, stock_by_unit_location in totals.items():
        if not stock_by_unit_location:
            continue
        unit_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for (unit, _location), quantity in stock_by_unit_location.items():
            unit_totals[unit] += quantity
        stock_text = ", ".join(f"{format_decimal(quantity)} {unit}".strip() for unit, quantity in sorted(unit_totals.items()))
        location_text = ", ".join(sorted(locations[key])) if locations[key] else "fără locație"
        result[key] = f"{stock_text}; locații: {location_text}"
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


def first_non_empty(*values: object) -> str:
    for value in values:
        text = str(value).strip()
        if text:
            return text
    return ""


def value_by_alias(values: dict[str, str], *aliases: str) -> str:
    normalized_aliases = {normalize_key(alias) for alias in aliases}
    for key, value in values.items():
        if normalize_key(key) in normalized_aliases:
            return str(value).strip()
    return ""


def pre_lot_matches_input(pre_lot_value: object, input_lot: object) -> bool:
    return shared_pre_lot_matches_input(pre_lot_value, input_lot)


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
