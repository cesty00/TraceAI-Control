from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.rules.pre_lot_classification import (
    PRE_LOT_MULTI_LOT_DIFFERENT,
    classify_pre_lot,
    normalize_match_value,
)
from src.rules.prd_table_mapping import (
    format_decimal,
    merged_values,
    parse_decimal,
    value_by_alias,
)

NEEDS_REVIEW = "needs_review"
CONFIRMED = "confirmed"


@dataclass(frozen=True)
class PrdConsumptionContext:
    code: str
    lot: str
    name: str
    quantity: str
    unit: str


@dataclass(frozen=True)
class PreLotPrdCandidate:
    product_code: str
    audited_lot: str
    matched_token: str
    pre_lot_value: str
    order_number: str
    order_quantity_total: str
    order_unit: str
    source_name: str
    sheet_name: str | None
    row_number: int | None
    consumptions: tuple[PrdConsumptionContext, ...]


@dataclass(frozen=True)
class WmsQuantityConfirmation:
    operation: str
    reason: str
    quantity: str
    unit: str


@dataclass(frozen=True)
class WmsFinishedGoodConfirmation:
    product_code: str
    audited_lot: str
    status: str
    has_exact_confirmation: bool
    confirmations: tuple[WmsQuantityConfirmation, ...]


@dataclass(frozen=True)
class InternalMultiLotPrdCandidateSelection:
    candidate: PreLotPrdCandidate
    wms_confirmation: WmsFinishedGoodConfirmation
    status: str


def _multi_lot_different_has_exact_token(pre_lot_value: object, audited_lot: object) -> bool:
    normalized_audited_lot = normalize_match_value(audited_lot)
    if not normalized_audited_lot:
        return False

    classification = classify_pre_lot(pre_lot_value)
    if classification.kind != PRE_LOT_MULTI_LOT_DIFFERENT:
        return False
    return normalized_audited_lot in classification.tokens


def _extract_multi_lot_prd_candidates(dataset: Any, product_code: object, audited_lot: object) -> tuple[PreLotPrdCandidate, ...]:
    normalized_code = normalize_match_value(product_code)
    normalized_lot = normalize_match_value(audited_lot)
    if not normalized_code or not normalized_lot:
        return ()

    grouped: dict[tuple[str, str, str, str, str, str | None, int | None, str], dict[str, Any]] = {}
    for table in getattr(dataset, "tables", []):
        if getattr(table, "source_key", None) != "production":
            continue
        for row in getattr(table, "rows", []):
            values = merged_values(row)
            row_code = normalize_match_value(value_by_alias(values, "pre_cod_articol", "PRE_Cod Articol"))
            if row_code != normalized_code:
                continue
            if not _multi_lot_different_has_exact_token(value_by_alias(values, "pre_lot", "PRE_LOT"), normalized_lot):
                continue

            classification = classify_pre_lot(value_by_alias(values, "pre_lot", "PRE_LOT"))
            order_number = value_by_alias(values, "numar_comanda", "Numar Comanda")
            order_quantity_total = value_by_alias(values, "pre_cantitate_predare", "PRE_Cantitate Predare")
            order_unit = value_by_alias(values, "pre_u_m", "PRE_U.M.")
            key = (
                row_code,
                normalized_lot,
                order_number,
                order_quantity_total,
                order_unit,
                getattr(table, "source_name", ""),
                getattr(table, "sheet_name", None),
                getattr(row, "row_number", None),
                classification.normalized_value,
            )
            bucket = grouped.setdefault(
                key,
                {
                    "consumptions": defaultdict(lambda: {"quantity": Decimal("0"), "name": "", "unit": ""}),
                },
            )
            component_code = value_by_alias(values, "con_cod_articol", "CON_Cod Articol")
            component_lot = value_by_alias(values, "con_lot", "CON_LOT")
            component_name = value_by_alias(values, "con_denumire_articol", "CON_Denumire Articol")
            component_unit = value_by_alias(values, "con_u_m", "CON_U.M.")
            component_quantity = parse_decimal(value_by_alias(values, "con_cantitate_consumata", "CON_Cantitate Consumata"))
            if component_code and component_lot and component_quantity is not None:
                consumption = bucket["consumptions"][(component_code, component_lot)]
                consumption["quantity"] += component_quantity
                if component_name:
                    consumption["name"] = component_name
                if component_unit:
                    consumption["unit"] = component_unit

    candidates: list[PreLotPrdCandidate] = []
    for (
        row_code,
        matched_lot,
        order_number,
        order_quantity_total,
        order_unit,
        source_name,
        sheet_name,
        row_number,
        normalized_pre_lot,
    ), bucket in sorted(grouped.items()):
        consumptions = tuple(
            PrdConsumptionContext(
                code=component_code,
                lot=component_lot,
                name=details["name"],
                quantity=format_decimal(details["quantity"]),
                unit=details["unit"],
            )
            for (component_code, component_lot), details in sorted(bucket["consumptions"].items())
        )
        candidates.append(
            PreLotPrdCandidate(
                product_code=row_code,
                audited_lot=matched_lot,
                matched_token=matched_lot,
                pre_lot_value=normalized_pre_lot,
                order_number=order_number,
                order_quantity_total=order_quantity_total,
                order_unit=order_unit,
                source_name=source_name,
                sheet_name=sheet_name,
                row_number=row_number,
                consumptions=consumptions,
            )
        )
    return tuple(candidates)


def _confirm_finished_good_wms_quantity(dataset: Any, product_code: object, audited_lot: object) -> WmsFinishedGoodConfirmation:
    normalized_code = normalize_match_value(product_code)
    normalized_lot = normalize_match_value(audited_lot)
    confirmations: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0"))

    for table in getattr(dataset, "tables", []):
        if getattr(table, "source_key", None) != "wms":
            continue
        for row in getattr(table, "rows", []):
            values = merged_values(row)
            row_code = normalize_match_value(value_by_alias(values, "cod_articol", "Cod articol"))
            row_lot = normalize_match_value(value_by_alias(values, "lot", "Lot"))
            if row_code != normalized_code or row_lot != normalized_lot:
                continue
            quantity = parse_decimal(value_by_alias(values, "cantitate", "Cantitate"))
            if quantity is None:
                continue
            operation = value_by_alias(values, "tip_operatiune", "Tip operatiune")
            reason = value_by_alias(values, "cod_motiv", "Cod-motiv")
            unit = value_by_alias(values, "um", "UM")
            confirmations[(operation, reason, unit)] += quantity

    confirmation_rows = tuple(
        WmsQuantityConfirmation(
            operation=operation,
            reason=reason,
            quantity=format_decimal(quantity),
            unit=unit,
        )
        for (operation, reason, unit), quantity in sorted(confirmations.items())
    )
    has_exact_confirmation = bool(confirmation_rows)
    return WmsFinishedGoodConfirmation(
        product_code=normalized_code,
        audited_lot=normalized_lot,
        status=CONFIRMED if has_exact_confirmation else NEEDS_REVIEW,
        has_exact_confirmation=has_exact_confirmation,
        confirmations=confirmation_rows,
    )


def _select_internal_multi_lot_prd_candidates(dataset: Any, product_code: object, audited_lot: object) -> tuple[InternalMultiLotPrdCandidateSelection, ...]:
    candidates = _extract_multi_lot_prd_candidates(dataset, product_code, audited_lot)
    if not candidates:
        return ()

    confirmation = _confirm_finished_good_wms_quantity(dataset, product_code, audited_lot)
    return tuple(
        InternalMultiLotPrdCandidateSelection(
            candidate=candidate,
            wms_confirmation=confirmation,
            status=confirmation.status,
        )
        for candidate in candidates
    )


def _confirmed_multi_lot_prd_order_numbers(dataset: Any, product_code: object, audited_lot: object) -> tuple[str, ...]:
    selections = _select_internal_multi_lot_prd_candidates(dataset, product_code, audited_lot)
    if not selections:
        return ()

    confirmed_order_numbers: list[str] = []
    seen_orders: set[str] = set()
    for selection in selections:
        if selection.status != CONFIRMED:
            continue
        order_number = str(selection.candidate.order_number).strip()
        normalized_order = normalize_match_value(order_number)
        if not normalized_order or normalized_order in seen_orders:
            continue
        seen_orders.add(normalized_order)
        confirmed_order_numbers.append(order_number)
    return tuple(confirmed_order_numbers)
