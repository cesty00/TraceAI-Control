"""Source-specific report table mapping for TraceabilityCase.

The generic selected-record classifier is intentionally conservative, but PRD
exports contain explicit PRE_* and CON_* columns. These helpers aggregate those
columns into stable report-table rows before the DOCX report is rendered.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

ALISOL_AUXILIARY_OBSERVATION = "ALISOL este tratat ca auxiliar / gaz tehnologic, nu ca materie primă alimentară."
RAW_MATERIAL_ROLE = "materie primă alimentară"
PACKAGING_ROLE = "ambalaj"

PACKAGING_TERMS = (
    "ambalaj",
    "ambalaje",
    "etichete",
    "eticheta",
    "etichetă",
    "folie",
    "film",
    "cutie",
    "caserole",
    "capac",
    "punga",
    "pungă",
    "carton",
    "pad",
    "absorbante",
)
RAW_MATERIAL_TERMS = (
    "materie prima",
    "materie primă",
    "materii prime",
    "ingredient",
    "refrigerat-p",
    "peste",
    "pește",
    "file",
    "creveti",
    "creveți",
    "pastrav",
    "păstrăv",
    "somon",
    "dorada",
    "ton",
    "calamar",
    "scoici",
)
AUXILIARY_TERMS = ("alisol", "gaz")


@dataclass(frozen=True)
class ReportRowPayload:
    values: dict[str, str]
    source_key: str | None
    source_name: str | None
    sheet_name: str | None
    row_number: int | None


def build_source_specific_rows(result: Any) -> dict[str, list[ReportRowPayload]]:
    """Build report rows from known source schemas.

    Returns rows for production, deliveries, PRD components, WMS receipts and
    stock. Values are aggregated conservatively: quantities are summed only when
    a clear Decimal can be parsed, and grouping keeps source units separate.
    """

    nomenclator = build_nomenclator_index(result.core.normalized_dataset)
    selected_records = list(result.core.selection.records)
    return {
        "production": build_prd_production_rows(selected_records),
        "finished_goods_deliveries": build_wms_delivery_rows(selected_records),
        "raw_materials": build_prd_component_rows(selected_records, nomenclator, "raw_material"),
        "packaging": build_prd_component_rows(selected_records, nomenclator, "packaging"),
        "auxiliaries_gas": build_prd_component_rows(selected_records, nomenclator, "auxiliary"),
        "wms_receipts": build_wms_receipt_rows(selected_records),
        "prd_consumptions": build_prd_consumption_rows(selected_records),
        "stock": build_stock_rows(selected_records),
    }


def build_prd_production_rows(records: list[Any]) -> list[ReportRowPayload]:
    grouped: dict[tuple[str, str, str, str, str], ReportRowPayload] = {}
    for record in records:
        if record.source_key != "production":
            continue
        values = merged_values(record)
        code = value_by_alias(values, "pre_cod_articol")
        lot = value_by_alias(values, "pre_lot")
        order = value_by_alias(values, "numar_comanda")
        quantity = value_by_alias(values, "pre_cantitate_predare")
        unit = value_by_alias(values, "pre_u_m")
        if not code or not lot or not order:
            continue
        key = (code, lot, order, quantity, unit)
        grouped.setdefault(
            key,
            ReportRowPayload(
                {
                    "Cod": code,
                    "Lot": lot,
                    "Comandă": order,
                    "Cantitate": quantity,
                    "UM": unit,
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
        if record.source_key != "production":
            continue
        values = merged_values(record)
        code = value_by_alias(values, "con_cod_articol")
        lot = value_by_alias(values, "con_lot")
        order = value_by_alias(values, "numar_comanda")
        unit = value_by_alias(values, "con_u_m")
        quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata"))
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
        if record.source_key != "production":
            continue
        values = merged_values(record)
        code = value_by_alias(values, "con_cod_articol")
        lot = value_by_alias(values, "con_lot")
        name = value_by_alias(values, "con_denumire_articol")
        unit = value_by_alias(values, "con_u_m")
        quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata"))
        if not code or not lot or quantity is None:
            continue
        detected_category = classify_component(code, name, nomenclator.get(code, ""))
        if detected_category != category:
            continue
        key = (code, lot, name, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "orders": set(), "record": record})
        bucket["quantity"] += quantity
        order = value_by_alias(values, "numar_comanda")
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
        operation = value_by_alias(values, "tip_operatiune")
        if operation.casefold() != "livrare":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda")
        document = value_by_alias(values, "document_comanda")
        client = value_by_alias(values, "partener")
        unit = value_by_alias(values, "um")
        key = (order, document, client, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": record})
        bucket["quantity"] += quantity
    rows = []
    for (order, document, client, unit), bucket in sorted(buckets.items()):
        record = bucket["record"]
        rows.append(
            ReportRowPayload(
                {"Numar comanda": order, "Document comanda": document, "Client": client, "Cantitate": format_decimal(bucket["quantity"]), "UM": unit},
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            )
        )
    return rows


def build_wms_receipt_rows(records: list[Any]) -> list[ReportRowPayload]:
    buckets: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for record in records:
        if record.source_key != "wms":
            continue
        values = merged_values(record)
        operation = value_by_alias(values, "tip_operatiune")
        if operation.casefold() != "receptie":
            continue
        quantity = parse_decimal(value_by_alias(values, "cantitate"))
        if quantity is None:
            continue
        order = value_by_alias(values, "numar_comanda")
        document_in = value_by_alias(values, "document_intrare")
        document_order = value_by_alias(values, "document_comanda")
        supplier = value_by_alias(values, "partener")
        unit = value_by_alias(values, "um")
        key = (order, document_in, document_order, supplier, unit)
        bucket = buckets.setdefault(key, {"quantity": Decimal("0"), "record": record})
        bucket["quantity"] += quantity
    rows = []
    for (order, document_in, document_order, supplier, unit), bucket in sorted(buckets.items()):
        record = bucket["record"]
        rows.append(
            ReportRowPayload(
                {
                    "Numar comanda": order,
                    "Document intrare": document_in,
                    "Document comanda": document_order,
                    "Furnizor": supplier,
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
        rows.append(
            ReportRowPayload(
                {
                    "Cod": value_by_alias(values, "cod_articol", "cod", "Cod"),
                    "Lot": value_by_alias(values, "lot", "Lot"),
                    "Stoc": value_by_alias(values, "stoc", "Stoc"),
                    "UM": value_by_alias(values, "um", "u_m", "UM"),
                    "Locație": value_by_alias(values, "locatie", "locație", "depozit", "magazie", "Locație"),
                },
                record.source_key,
                record.source_name,
                record.sheet_name,
                record.row_number,
            )
        )
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


def value_by_alias(values: dict[str, str], *aliases: str) -> str:
    normalized_aliases = {normalize_key(alias) for alias in aliases}
    for key, value in values.items():
        if normalize_key(key) in normalized_aliases:
            return str(value).strip()
    return ""


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
