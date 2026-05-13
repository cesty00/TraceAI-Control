"""Source-specific report table mapping for TraceabilityCase.

PRD exports contain explicit PRE_* and CON_* columns. These helpers aggregate
those columns into stable report-table rows before the DOCX report is rendered.
The PRD mapper scans the normalized PRD table by PRE_Cod Articol + PRE_LOT,
matching the independent reference extractor instead of relying only on generic
selected records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.rules.pre_lot_classification import pre_lot_matches_input as shared_pre_lot_matches_input

ALISOL_AUXILIARY_OBSERVATION = "ALISOL este tratat ca auxiliar / gaz tehnologic, nu ca materie primă alimentară."
RAW_MATERIAL_ROLE = "materie primă alimentară"
MISSING = "FARA DATE IDENTIFICATE"
DATE_ALIASES = (
    "data", "data_operatiune", "data_operațiune", "data_miscare", "data_mișcare",
    "data_document", "data_doc", "data_livrare", "data_receptie", "data_recepție",
    "created_at", "date", "Data", "Data document", "Data livrare", "Data receptie",
)

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


@dataclass(frozen=True)
class ReportRowPayload:
    values: dict[str, str]
    source_key: str | None
    source_name: str
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


def build_source_specific_rows(result: Any) -> dict[str, list[ReportRowPayload]]:
    nomenclator = build_nomenclator_index(result.core.normalized_dataset)
    selected_records = list(result.core.selection.records)
    prd_rows = matching_prd_rows(result)

    return {
        "production": build_prd_production_rows(prd_rows),
        "finished_goods_deliveries": build_wms_delivery_rows(selected_records),
        "raw_materials": build_prd_component_rows(prd_rows, nomenclator, "raw_material"),
        "packaging": build_prd_component_rows(prd_rows, nomenclator, "packaging"),
        "auxiliaries_gas": build_prd_component_rows(prd_rows, nomenclator, "auxiliary"),
        "wms_receipts": build_wms_receipt_rows(selected_records),
        "prd_consumptions": build_prd_consumption_rows(prd_rows),
        "stock": build_stock_rows(selected_records),
    }


def matching_prd_rows(result: Any) -> list[SourceRow]:
    code = normalize_match_value(result.core.selection.input_code)
    lot = normalize_match_value(result.core.selection.input_lot)
    dataset = result.core.normalized_dataset
    rows: list[SourceRow] = []
    for table in getattr(dataset, "tables", []):
        if table.source_key != "production":
            continue
        for row in table.rows:
            values = dict(row.values)
            original_values = dict(getattr(row, "original_values", {}) or {})
            merged = dict(values)
            merged.update(original_values)
            if normalize_match_value(value_by_alias(merged, "pre_cod_articol", "PRE_Cod Articol")) != code:
                continue
            if not pre_lot_matches_input(value_by_alias(merged, "pre_lot", "PRE_LOT"), lot):
                continue
            rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, values, original_values))
    if rows:
        return rows

    from src.rules.pre_lot_multi_lot_prd_wms_split import (
        _confirmed_multi_lot_prd_order_numbers,
        _multi_lot_different_has_exact_token,
    )

    confirmed_orders = _confirmed_multi_lot_prd_order_numbers(dataset, result.core.selection.input_code, result.core.selection.input_lot)
    confirmed_order_keys = {
        normalize_match_value(order_number)
        for order_number in confirmed_orders
        if normalize_match_value(order_number)
    }
    if not confirmed_order_keys:
        return []

    fallback_rows: list[SourceRow] = []
    for table in getattr(dataset, "tables", []):
        if table.source_key != "production":
            continue
        for row in table.rows:
            values = dict(row.values)
            original_values = dict(getattr(row, "original_values", {}) or {})
            merged = dict(values)
            merged.update(original_values)
            if normalize_match_value(value_by_alias(merged, "pre_cod_articol", "PRE_Cod Articol")) != code:
                continue
            order_number = normalize_match_value(value_by_alias(merged, "numar_comanda", "Numar Comanda"))
            if order_number not in confirmed_order_keys:
                continue
            if not _multi_lot_different_has_exact_token(value_by_alias(merged, "pre_lot", "PRE_LOT"), lot):
                continue
            fallback_rows.append(SourceRow(table.source_key, table.source_name, table.sheet_name, row.row_number, values, original_values))
    return fallback_rows


def build_prd_production_rows(records: list[Any]) -> list[ReportRowPayload]:
    grouped: dict[tuple[str, str, str, str, str], ReportRowPayload] = {}
    for record in records:
        values = merged_values(record)
        code = value_by_alias(values, "pre_cod_articol", "PRE_Cod Articol")
        lot = value_by_alias(values, "pre_lot", "PRE_LOT")
        name = value_by_alias(values, "pre_denumire_articol", "PRE_Denumire Articol")
        order = value_by_alias(values, "numar_comanda", "Numar Comanda")
        quantity = value_by_alias(values, "pre_cantitate_predare", "PRE_Cantitate Predare")
        unit = value_by_alias(values, "pre_u_m", "PRE_U.M.")
        production_date = first_non_empty(value_by_alias(values, "data_productie", "data_producție", "data", "Data"), MISSING)
        ddm = first_non_empty(value_by_alias(values, "ddm", "data_durabilitatii_minimale", "data_durabilității_minimale", "Data durabilitatii minimale"), MISSING)
        if not code or not lot or not order:
            continue
        key = (code, lot, order, quantity, unit)
        grouped.setdefault(
            key,
            ReportRowPayload(
                {
                    "Cod": code,
                    "Lot": lot,
                    "Denumire": name,
                    "Comandă": order,
                    "Cantitate": quantity,
                    "UM": unit,
                    "Data producției": production_date,
                    "DDM": ddm,
                    "Observații": "PRD PRE_Cantitate Predare; rând unic pe comandă producție.",
                },
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            ),
        )
    return sorted(grouped.values(), key=lambda row: row.values.get("Comandă", ""))


def build_prd_consumption_rows(records: list[Any]) -> list[ReportRowPayload]:
    buckets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        values = merged_values(record)
        code = value_by_alias(values, "con_cod_articol", "CON_Cod Articol")
        lot = value_by_alias(values, "con_lot", "CON_LOT")
        order = value_by_alias(values, "numar_comanda", "Numar Comanda")
        unit = value_by_alias(values, "con_u_m", "CON_U.M.")
        quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata", "CON_Cantitate Consumata"))
        if not code or not lot or quantity is None:
            continue
        key = (code, lot, order, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": record})
        bucket["quantity"] += quantity
    rows = []
    for (code, lot, order, unit), bucket in sorted(buckets.items()):
        record = bucket["record"]
        rows.append(
            ReportRowPayload(
                {"Cod": code, "Lot": lot, "Comandă producție": order, "Cantitate": format_decimal(bucket["quantity"]), "UM": unit},
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            )
        )
    return rows


def build_prd_component_rows(records: list[Any], nomenclator: dict[str, str], category: str) -> list[ReportRowPayload]:
    buckets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        values = merged_values(record)
        code = value_by_alias(values, "con_cod_articol", "CON_Cod Articol")
        lot = value_by_alias(values, "con_lot", "CON_LOT")
        name = value_by_alias(values, "con_denumire_articol", "CON_Denumire Articol")
        unit = value_by_alias(values, "con_u_m", "CON_U.M.")
        quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata", "CON_Cantitate Consumata"))
        if not code or not lot or quantity is None:
            continue
        detected_category = classify_component(code, name, nomenclator.get(code, ""))
        if detected_category != category:
            continue
        key = (code, lot, name, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "orders": set(), "record": record})
        bucket["quantity"] += quantity
        order = value_by_alias(values, "numar_comanda", "Numar Comanda")
        if order:
            bucket["orders"].add(order)
    rows = []
    for (code, lot, name, unit), bucket in sorted(buckets.items()):
        record = bucket["record"]
        values = {"Cod": code, "Lot": lot, "Denumire": name, "Cantitate": format_decimal(bucket["quantity"]), "UM": unit}
        if category == "raw_material":
            values["Rol"] = RAW_MATERIAL_ROLE
        if category == "auxiliary":
            values["Observații"] = ALISOL_AUXILIARY_OBSERVATION
        rows.append(ReportRowPayload(values, record.source_key, record.source_name, record.sheet_name, record.row_number))
    return rows


def build_wms_delivery_rows(records: list[Any]) -> list[ReportRowPayload]:
    buckets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in records:
        if record.source_key != "wms":
            continue
        values = merged_values(record)
        operation = value_by_alias(values, "tip_operatiune", "Tip operatiune")
        if operation.casefold() != "livrare":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda", "Numar comanda")
        document = value_by_alias(values, "document_comanda", "Document comanda")
        client = value_by_alias(values, "partener", "Partener")
        unit = value_by_alias(values, "um", "UM")
        delivery_date = first_non_empty(value_by_alias(values, *DATE_ALIASES), MISSING)
        key = (order, document, client, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": record, "dates": set()})
        bucket["quantity"] += quantity
        if delivery_date != MISSING:
            bucket["dates"].add(delivery_date)
    rows = []
    for (order, document, client, unit), bucket in sorted(buckets.items()):
        record = bucket["record"]
        delivery_date = "; ".join(sorted(bucket["dates"])) if bucket["dates"] else MISSING
        rows.append(
            ReportRowPayload(
                {
                    "Numar comanda": order,
                    "Document comanda": document,
                    "Client": client,
                    "Data livrare": delivery_date,
                    "Data document": delivery_date,
                    "Cantitate": format_decimal(bucket["quantity"]),
                    "UM": unit,
                },
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            )
        )
    return rows


def build_wms_receipt_rows(records: list[Any]) -> list[ReportRowPayload]:
    buckets: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for record in records:
        if record.source_key != "wms":
            continue
        values = merged_values(record)
        operation = value_by_alias(values, "tip_operatiune", "Tip operatiune")
        if operation.casefold() != "receptie":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda", "Numar comanda")
        document_in = value_by_alias(values, "document_intrare", "Document intrare")
        document_order = value_by_alias(values, "document_comanda", "Document comanda")
        supplier = value_by_alias(values, "partener", "Partener")
        unit = value_by_alias(values, "um", "UM")
        receipt_date = first_non_empty(value_by_alias(values, *DATE_ALIASES), MISSING)
        key = (order, document_in, document_order, supplier, unit, receipt_date)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": record})
        bucket["quantity"] += quantity
    rows = []
    for (order, document_in, document_order, supplier, unit, receipt_date), bucket in sorted(buckets.items()):
        record = bucket["record"]
        rows.append(
            ReportRowPayload(
                {
                    "Numar comanda": order,
                    "Document intrare": document_in,
                    "Document comanda": document_order,
                    "Furnizor": supplier,
                    "Data recepție": receipt_date,
                    "Data document": receipt_date,
                    "Cantitate": format_decimal(bucket["quantity"]),
                    "UM": unit,
                },
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            )
        )
    return rows


def build_stock_rows(records: list[Any]) -> list[ReportRowPayload]:
    rows = []
    for record in records:
        if record.source_key != "stock":
            continue
        values = merged_values(record)
        rows.append(ReportRowPayload({"Cod": value_by_alias(values, "cod_articol", "cod", "Cod"), "Lot": value_by_alias(values, "lot", "Lot"), "Stoc": value_by_alias(values, "stoc", "Stoc"), "UM": value_by_alias(values, "um", "u_m", "UM"), "Locație": value_by_alias(values, "locatie", "locație", "depozit", "magazie", "Locație")}, record.source_key, record.source_name, record.sheet_name, record.row_number))
    return rows


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
