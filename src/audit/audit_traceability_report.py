"""Audit-level traceability report DTO.

This module is the technical bridge between the existing TraceabilityCase and
the audit report format validated for DS099904011 / 103.26. It intentionally
keeps presentation concerns out of the data model: DOCX renderers should consume
AuditTraceabilityReport, not raw normalized tables.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Iterable

from src.rules.traceability_case import TraceabilityCase, TraceabilityReportTable, TraceabilityTableRow

STATUS_PASS = "PASS"
STATUS_PASS_WITH_OBSERVATIONS = "PASS_WITH_OBSERVATIONS"
STATUS_INCOMPLETE = "INCOMPLETE"
STATUS_FAIL = "FAIL"

THIRD_PARTY_NO = "NU"
THIRD_PARTY_YES = "DA"
THIRD_PARTY_UNKNOWN = "NECLAR"
THIRD_PARTY_NOT_APPLICABLE = "NU_SE_APLICA"
MISSING = "FARA DATE IDENTIFICATE"
DEFAULT_DATA_QUALITY_SUMMARY = {
    "status": "NOT_AVAILABLE",
    "source_count": 0,
    "sources_found": 0,
    "error_count": 0,
    "warning_count": 0,
    "issue_count": 0,
}
DATE_FIELD_ALIASES = (
    "Data", "Dată", "Data document", "Dată document", "Data livrare", "Dată livrare",
    "Data recepție", "Dată recepție", "Data receptie", "Data producției", "Data productie",
    "data", "data_document", "data_livrare", "data_receptie", "data_productie",
)


@dataclass(frozen=True)
class AuditExercise:
    code: str
    lot: str
    product_name: str
    case_type: str
    data_sources: list[str]
    traceability_result: str


@dataclass(frozen=True)
class FinishedProductBalance:
    prd_produced_quantity: str
    prd_produced_um: str
    wms_production_out_quantity: str
    wms_production_out_um: str
    wms_delivered_quantity: str
    wms_delivered_um: str
    stock_quantity: str
    stock_um: str
    adjustments_quantity: str
    adjustments_um: str
    balance_status: str
    balance_observation: str


@dataclass(frozen=True)
class FinishedProductDelivery:
    order_number: str
    document_number: str
    client: str
    delivery_date: str
    quantity: str
    um: str
    rows: str
    source_rows: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UpstreamMaterialLine:
    category: str
    code: str
    lot: str
    name: str
    quantity_consumed: str
    um: str
    receipt_summary: str
    supplier_summary: str
    document_summary: str
    third_party_delivery_status: str
    third_party_delivery_details: str
    stock_at_moment: str
    stock_um: str
    observations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProductionOrderTrace:
    production_order: str
    finished_product_code: str
    finished_product_lot: str
    finished_product_name: str
    prd_quantity: str
    prd_um: str
    wms_production_out_quantity: str
    wms_production_out_um: str
    associated_delivery: str
    production_date: str = MISSING
    raw_materials: list[UpstreamMaterialLine] = field(default_factory=list)
    packaging: list[UpstreamMaterialLine] = field(default_factory=list)
    auxiliaries_gas: list[UpstreamMaterialLine] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceLotFlow:
    category: str
    code: str
    lot: str
    name: str
    receipt_total: str
    receipt_documents: str
    consumed_in_audited_lot: str
    consumed_in_other_orders: str
    third_party_delivered_total: str
    adjustments_total: str
    stock_at_moment: str
    flow_status: str
    observation: str


@dataclass(frozen=True)
class PhysicalDocumentRequirement:
    document_area: str
    document_type: str
    document_reference: str
    related_code: str
    related_lot: str
    related_order: str
    why_needed: str
    status: str


@dataclass(frozen=True)
class AuditConclusion:
    status: str
    summary: str
    observations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditTraceabilityReport:
    exercise: AuditExercise
    balance: FinishedProductBalance
    downstream: list[FinishedProductDelivery]
    upstream: list[UpstreamMaterialLine]
    production_orders: list[ProductionOrderTrace]
    source_lot_flows: list[SourceLotFlow]
    physical_documents: list[PhysicalDocumentRequirement]
    observations: list[str]
    conclusion: AuditConclusion
    data_quality: dict[str, Any] = field(default_factory=dict)


def build_audit_traceability_report(traceability_case: TraceabilityCase) -> AuditTraceabilityReport:
    exercise = AuditExercise(
        code=traceability_case.subject.code,
        lot=traceability_case.subject.lot,
        product_name=detect_product_name(traceability_case),
        case_type=traceability_case.subject.case_type,
        data_sources=format_sources(traceability_case),
        traceability_result=detect_report_status(traceability_case),
    )
    downstream = build_downstream(traceability_case.report_tables.finished_goods_deliveries)
    production_orders = build_production_orders(traceability_case)
    upstream = build_upstream(traceability_case, production_orders)
    balance = build_finished_product_balance(traceability_case, downstream, production_orders)
    source_lot_flows = build_source_lot_flows(upstream)
    documents = build_physical_document_requirements(exercise, downstream, upstream, production_orders)
    observations = collect_observations(traceability_case, upstream, production_orders, balance)
    conclusion = AuditConclusion(
        status=exercise.traceability_result,
        summary=build_conclusion_summary(exercise, balance, downstream, upstream, production_orders),
        observations=observations,
    )
    return AuditTraceabilityReport(
        exercise=exercise,
        balance=balance,
        downstream=downstream,
        upstream=upstream,
        production_orders=production_orders,
        source_lot_flows=source_lot_flows,
        physical_documents=documents,
        observations=observations,
        conclusion=conclusion,
        data_quality=normalize_data_quality_summary(traceability_case.sections.get("data_quality")),
    )


def normalize_data_quality_summary(data_quality: Any) -> dict[str, Any]:
    """Return the compact Data Quality summary using a stable report shape."""

    source = data_quality if isinstance(data_quality, dict) else {}
    summary = dict(DEFAULT_DATA_QUALITY_SUMMARY)
    for key in summary:
        if key in source:
            summary[key] = source[key]
    return summary


def build_downstream(table: TraceabilityReportTable) -> list[FinishedProductDelivery]:
    deliveries: list[FinishedProductDelivery] = []
    for row in table.rows:
        deliveries.append(
            FinishedProductDelivery(
                order_number=value(row, "Numar comanda"),
                document_number=value(row, "Document comanda"),
                client=value(row, "Client"),
                delivery_date=first_existing_value(row, "Data livrare", "Data document", *DATE_FIELD_ALIASES),
                quantity=value(row, "Cantitate"),
                um=value(row, "UM"),
                rows="1",
                source_rows=[format_source(row)],
            )
        )
    return deliveries


def build_upstream(traceability_case: TraceabilityCase, production_orders: list[ProductionOrderTrace]) -> list[UpstreamMaterialLine]:
    order_upstream = aggregate_upstream_from_orders(production_orders)
    if order_upstream:
        return order_upstream
    rows: list[UpstreamMaterialLine] = []
    rows.extend(upstream_from_table(traceability_case.report_tables.raw_materials, "raw_material", include_third_party=True))
    rows.extend(upstream_from_table(traceability_case.report_tables.packaging, "packaging", include_third_party=False))
    rows.extend(upstream_from_table(traceability_case.report_tables.auxiliaries_gas, "auxiliary_gas", include_third_party=False))
    return rows


def aggregate_upstream_from_orders(production_orders: list[ProductionOrderTrace]) -> list[UpstreamMaterialLine]:
    lines: list[UpstreamMaterialLine] = []
    for order in production_orders:
        lines.extend(order.raw_materials)
        lines.extend(order.packaging)
        lines.extend(order.auxiliaries_gas)
    if not lines:
        return []
    grouped: dict[tuple[str, str, str, str, str], list[UpstreamMaterialLine]] = defaultdict(list)
    for line in lines:
        grouped[(line.category, line.code, line.lot, line.name, line.um)].append(line)
    aggregated: list[UpstreamMaterialLine] = []
    for (category, code, lot, name, um), group in sorted(grouped.items()):
        totals = sum_by_unit((line.quantity_consumed, line.um) for line in group)
        quantity, normalized_um = single_total_or_missing(totals)
        if normalized_um == MISSING:
            normalized_um = um
        status = merge_third_party_status(line.third_party_delivery_status for line in group)
        details = merge_third_party_details(status, [line.third_party_delivery_details for line in group])
        receipt_summary = merge_text_summaries(line.receipt_summary for line in group)
        structured_received_quantity = merge_text_summaries(receipt_received_quantity(line) for line in group)
        structured_receipt_date = merge_text_summaries(receipt_date_value(line) for line in group)
        structured_supplier = merge_text_summaries(receipt_supplier_value(line) for line in group)
        stock_summary = merge_text_summaries(line.stock_at_moment for line in group)
        observations = dedupe([observation for line in group for observation in line.observations])
        if status == THIRD_PARTY_NO and category == "raw_material":
            observations.append("Nu au fost identificate livrări către terți pentru lotul de materie primă în datele disponibile.")
        if receipt_summary == MISSING:
            observations.append("Nu au fost identificate recepții WMS pentru lotul sursă în datele disponibile.")
        if stock_summary == MISSING:
            observations.append("Lotul sursă nu apare în stocul la moment sau stocul nu a fost mapat încă.")
        if status == THIRD_PARTY_NOT_APPLICABLE and category != "raw_material" and not observations:
            observations.append("Verificarea livrărilor către terți nu se aplică pentru această categorie.")
        aggregated_line = UpstreamMaterialLine(
            category=category,
            code=code,
            lot=lot,
            name=name,
            quantity_consumed=quantity,
            um=normalized_um,
            receipt_summary=receipt_summary,
            supplier_summary=receipt_summary,
            document_summary=receipt_summary,
            third_party_delivery_status=status,
            third_party_delivery_details=details,
            stock_at_moment=stock_summary,
            stock_um="",
            observations=dedupe(observations),
        )
        set_structured_receipt_fields(
            aggregated_line,
            received_quantity=structured_received_quantity,
            receipt_date=structured_receipt_date,
            supplier=structured_supplier,
        )
        aggregated.append(aggregated_line)
    return aggregated


def upstream_from_table(table: TraceabilityReportTable, category: str, include_third_party: bool) -> list[UpstreamMaterialLine]:
    lines: list[UpstreamMaterialLine] = []
    for row in table.rows:
        observations: list[str] = []
        third_party_status = THIRD_PARTY_UNKNOWN if include_third_party else THIRD_PARTY_NOT_APPLICABLE
        third_party_details = MISSING if include_third_party else "Nu se aplică"
        if not include_third_party:
            observations.append("Verificarea livrărilor către terți nu se aplică pentru această categorie.")
        lines.append(
            UpstreamMaterialLine(
                category=category,
                code=value(row, "Cod"),
                lot=value(row, "Lot"),
                name=value(row, "Denumire"),
                quantity_consumed=value(row, "Cantitate"),
                um=value(row, "UM"),
                receipt_summary=MISSING,
                supplier_summary=MISSING,
                document_summary=MISSING,
                third_party_delivery_status=third_party_status,
                third_party_delivery_details=third_party_details,
                stock_at_moment=MISSING,
                stock_um="",
                observations=observations,
            )
        )
    return lines


def build_production_orders(traceability_case: TraceabilityCase) -> list[ProductionOrderTrace]:
    order_table = traceability_case.report_tables.order_traceability
    if order_table is None or not order_table.rows:
        return production_orders_from_summary(traceability_case)
    by_order: dict[str, list[TraceabilityTableRow]] = defaultdict(list)
    for row in order_table.rows:
        by_order[value(row, "Comandă producție")].append(row)
    result: list[ProductionOrderTrace] = []
    for order in sorted(by_order):
        rows = by_order[order]
        first = rows[0]
        raw_materials: list[UpstreamMaterialLine] = []
        packaging: list[UpstreamMaterialLine] = []
        auxiliaries: list[UpstreamMaterialLine] = []
        observations: list[str] = []
        for row in rows:
            line = upstream_line_from_order_row(row)
            category = value(row, "Categorie consum")
            if category == "Materie primă alimentară":
                raw_materials.append(line)
                if line.third_party_delivery_status == THIRD_PARTY_NO:
                    observations.append(f"Materia primă {line.code}/{line.lot}: fără livrări către terți identificate.")
            elif category == "Ambalaj":
                packaging.append(line)
            elif category == "Auxiliar / gaz":
                auxiliaries.append(line)
            else:
                observations.append(f"Consum cu categorie neclară: {line.code}/{line.lot}.")
        out_quantity, out_um = split_quantity_unit(value(first, "WMS production-out"))
        result.append(
            ProductionOrderTrace(
                production_order=order,
                finished_product_code=traceability_case.subject.code,
                finished_product_lot=traceability_case.subject.lot,
                finished_product_name=value(first, "Produs finit"),
                prd_quantity=value(first, "Cantitate produs finit"),
                prd_um=value(first, "UM produs finit"),
                wms_production_out_quantity=out_quantity,
                wms_production_out_um=out_um,
                associated_delivery=value(first, "Livrare produs finit asociată"),
                production_date=first_existing_value(first, "Data producției", "Data productie", *DATE_FIELD_ALIASES),
                raw_materials=raw_materials,
                packaging=packaging,
                auxiliaries_gas=auxiliaries,
                observations=dedupe(observations),
            )
        )
    return result


def production_orders_from_summary(traceability_case: TraceabilityCase) -> list[ProductionOrderTrace]:
    result: list[ProductionOrderTrace] = []
    for row in traceability_case.report_tables.production.rows:
        result.append(
            ProductionOrderTrace(
                production_order=value(row, "Comandă"),
                finished_product_code=value(row, "Cod"),
                finished_product_lot=value(row, "Lot"),
                finished_product_name=value(row, "Denumire"),
                prd_quantity=value(row, "Cantitate"),
                prd_um=value(row, "UM"),
                wms_production_out_quantity=MISSING,
                wms_production_out_um=MISSING,
                associated_delivery=MISSING,
                production_date=first_existing_value(row, "Data producției", "Data productie", *DATE_FIELD_ALIASES),
                observations=["Detalierea pe comenzi nu este disponibilă în TraceabilityCase."],
            )
        )
    return result


def upstream_line_from_order_row(row: TraceabilityTableRow) -> UpstreamMaterialLine:
    third_party_details = value(row, "Livrări consum către terți")
    third_party_status = normalize_third_party_status(third_party_details)
    category = category_from_order_label(value(row, "Categorie consum"))
    receipt_summary = value(row, "Recepții WMS consum")
    stock_summary = value(row, "Stoc consum la moment")
    observations: list[str] = []
    if third_party_status == THIRD_PARTY_UNKNOWN:
        observations.append("Status livrări către terți neclar în datele disponibile.")
    elif third_party_status == THIRD_PARTY_NOT_APPLICABLE:
        observations.append("Verificarea livrărilor către terți nu se aplică pentru această categorie.")
    if receipt_summary == MISSING:
        observations.append("Nu au fost identificate recepții WMS pentru acest lot consumat.")
    if stock_summary == MISSING:
        observations.append("Lotul consumat nu apare în stocul la moment sau stocul nu este disponibil.")
    line = UpstreamMaterialLine(
        category=category,
        code=value(row, "Cod consum"),
        lot=value(row, "Lot consum"),
        name=value(row, "Denumire consum"),
        quantity_consumed=value(row, "Cantitate consum"),
        um=value(row, "UM consum"),
        receipt_summary=receipt_summary,
        supplier_summary=receipt_summary,
        document_summary=receipt_summary,
        third_party_delivery_status=third_party_status,
        third_party_delivery_details=third_party_details,
        stock_at_moment=stock_summary,
        stock_um="",
        observations=observations,
    )
    set_structured_receipt_fields(
        line,
        received_quantity=structured_receipt_received_quantity(
            value(row, "Cantitate recepționată consum"),
            receipt_summary,
        ),
        receipt_date=structured_receipt_date(
            value(row, "Data recepție consum"),
            receipt_summary,
        ),
        supplier=structured_receipt_supplier(
            value(row, "Furnizor recepție consum"),
            receipt_summary,
        ),
    )
    return line


def structured_receipt_received_quantity(explicit_value: str, receipt_summary: str) -> str:
    if explicit_value and explicit_value != MISSING:
        return explicit_value
    return receipt_total_quantity_from_summary(receipt_summary)


def receipt_total_quantity_from_summary(receipt_summary: str) -> str:
    if not receipt_summary or receipt_summary == MISSING:
        return MISSING
    prefix = receipt_summary.split(";", 1)[0].strip()
    if not prefix.lower().startswith("total "):
        return MISSING
    quantity = prefix[len("total "):].strip()
    return quantity or MISSING


def structured_receipt_date(explicit_value: str, receipt_summary: str) -> str:
    if explicit_value and explicit_value != MISSING:
        return explicit_value
    return receipt_date_from_summary(receipt_summary)


def structured_receipt_supplier(explicit_value: str, receipt_summary: str) -> str:
    if explicit_value and explicit_value != MISSING:
        return explicit_value
    return receipt_supplier_from_summary(receipt_summary)


def receipt_first_example_from_summary(receipt_summary: str) -> str:
    if not receipt_summary or receipt_summary == MISSING:
        return ""
    first_example = receipt_summary.split(";", 1)[1].strip() if ";" in receipt_summary else receipt_summary.strip()
    return first_example.split(";", 1)[0].strip()


def receipt_date_from_summary(receipt_summary: str) -> str:
    first_example = receipt_first_example_from_summary(receipt_summary)
    match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b", first_example)
    return match.group(0) if match else MISSING


def receipt_supplier_from_summary(receipt_summary: str) -> str:
    first_example = receipt_first_example_from_summary(receipt_summary)
    if not first_example:
        return MISSING
    document = first_example.rsplit(": ", 1)[0].strip() if ": " in first_example else first_example
    detected_date = receipt_date_from_summary(receipt_summary)
    if detected_date != MISSING:
        document = document.replace(detected_date, "").strip(" /")
    parts = [part.strip() for part in document.split("/") if part.strip()]
    return parts[1] if len(parts) >= 2 else MISSING


def set_structured_receipt_fields(
    line: UpstreamMaterialLine,
    *,
    received_quantity: str = MISSING,
    receipt_date: str = MISSING,
    supplier: str = MISSING,
) -> None:
    object.__setattr__(line, "_receipt_received_quantity", received_quantity or MISSING)
    object.__setattr__(line, "_receipt_date_structured", receipt_date or MISSING)
    object.__setattr__(line, "_receipt_supplier_structured", supplier or MISSING)


def receipt_received_quantity(line: UpstreamMaterialLine) -> str:
    return getattr(line, "_receipt_received_quantity", MISSING)


def receipt_date_value(line: UpstreamMaterialLine) -> str:
    return getattr(line, "_receipt_date_structured", MISSING)


def receipt_supplier_value(line: UpstreamMaterialLine) -> str:
    return getattr(line, "_receipt_supplier_structured", MISSING)


def build_finished_product_balance(traceability_case: TraceabilityCase, downstream: list[FinishedProductDelivery], production_orders: list[ProductionOrderTrace]) -> FinishedProductBalance:
    prd_totals = sum_by_unit((order.prd_quantity, order.prd_um) for order in production_orders)
    production_out_totals = sum_by_unit((order.wms_production_out_quantity, order.wms_production_out_um) for order in production_orders)
    delivered_totals = sum_by_unit((delivery.quantity, delivery.um) for delivery in downstream)
    stock_totals = sum_by_unit((value(row, "Stoc"), value(row, "UM")) for row in traceability_case.report_tables.stock.rows)
    prd_quantity, prd_um = single_total_or_missing(prd_totals)
    out_quantity, out_um = single_total_or_missing(production_out_totals)
    delivered_quantity, delivered_um = single_total_or_missing(delivered_totals)
    stock_quantity, stock_um = single_total_or_missing(stock_totals)
    observations: list[str] = []
    status = STATUS_INCOMPLETE
    if prd_quantity != MISSING and out_quantity != MISSING:
        if quantities_equal(prd_quantity, out_quantity) and prd_um == out_um:
            status = STATUS_PASS
            observations.append("PRD produs coincide cu WMS PRODUCTION-OUT.")
        else:
            status = STATUS_PASS_WITH_OBSERVATIONS
            observations.append("PRD produs diferă de WMS PRODUCTION-OUT; verificare manuală necesară.")
    if delivered_quantity != MISSING:
        observations.append("Livrările sunt preluate din WMS și se evaluează în valoare absolută pentru reconciliere.")
    return FinishedProductBalance(prd_quantity, prd_um, out_quantity, out_um, delivered_quantity, delivered_um, stock_quantity, stock_um, MISSING, MISSING, status, " ".join(observations) if observations else MISSING)


def build_source_lot_flows(upstream: list[UpstreamMaterialLine]) -> list[SourceLotFlow]:
    return [
        SourceLotFlow(line.category, line.code, line.lot, line.name, line.receipt_summary, line.document_summary, f"{line.quantity_consumed} {line.um}", MISSING, line.third_party_delivery_details, MISSING, format_stock_summary(line.stock_at_moment, line.stock_um), "documentat parțial" if line.receipt_summary == MISSING else "documentat", "; ".join(line.observations) if line.observations else MISSING)
        for line in upstream
    ]


def build_physical_document_requirements(exercise: AuditExercise, downstream: list[FinishedProductDelivery], upstream: list[UpstreamMaterialLine], production_orders: list[ProductionOrderTrace]) -> list[PhysicalDocumentRequirement]:
    documents: list[PhysicalDocumentRequirement] = []
    for order in production_orders:
        documents.append(PhysicalDocumentRequirement("PRD", "Comandă / raport producție", order.production_order, exercise.code, exercise.lot, order.production_order, "Confirmă producția și consumurile pe comandă.", "required"))
    for delivery in downstream:
        documents.append(PhysicalDocumentRequirement("WMS", "Document livrare produs finit", delivery.document_number, exercise.code, exercise.lot, delivery.order_number, "Confirmă livrarea aval către client.", "required"))
    for line in upstream:
        documents.append(PhysicalDocumentRequirement("NIR" if line.category == "raw_material" else "WMS", "Document intrare / recepție lot sursă", line.document_summary, line.code, line.lot, MISSING, "Confirmă intrarea lotului sursă folosit în lotul auditat.", "required" if line.category in {"raw_material", "packaging"} else "recommended"))
    return documents


def collect_observations(traceability_case: TraceabilityCase, upstream: list[UpstreamMaterialLine], production_orders: list[ProductionOrderTrace], balance: FinishedProductBalance) -> list[str]:
    observations = list(traceability_case.observations)
    if is_incomplete_finished_product_case(traceability_case):
        observations.append(
            "Raport preliminar/incomplet: pentru produs finit lipsesc una sau mai multe dovezi esențiale (PRD, WMS production-out, amonte)."
        )
    if balance.balance_observation != MISSING:
        observations.append(balance.balance_observation)
    if any(line.third_party_delivery_status == THIRD_PARTY_NO for line in upstream if line.category == "raw_material"):
        observations.append("Pentru cel puțin un lot de materie primă nu au fost identificate livrări către terți.")
    if any(line.receipt_summary != MISSING for line in upstream):
        observations.append("Recepțiile WMS disponibile pentru loturile consumate au fost preluate în tabelul amonte.")
    if any(line.stock_at_moment != MISSING for line in upstream):
        observations.append("Stocul la moment disponibil pentru loturile consumate a fost preluat în tabelul amonte.")
    if any(not order.associated_delivery or order.associated_delivery == MISSING for order in production_orders):
        observations.append("Unele comenzi nu au livrare produs finit asociată explicit în TraceabilityCase.")
    return dedupe(observations)


def build_conclusion_summary(exercise: AuditExercise, balance: FinishedProductBalance, downstream: list[FinishedProductDelivery], upstream: list[UpstreamMaterialLine], production_orders: list[ProductionOrderTrace]) -> str:
    if exercise.traceability_result == STATUS_INCOMPLETE:
        return (
            f"Raport preliminar/incomplet pentru {exercise.code} / {exercise.lot}. "
            "Lipsesc una sau mai multe dovezi esențiale pentru produs finit: PRD, WMS production-out sau amonte. "
            f"Comenzi identificate: {len(production_orders)}. Livrări aval: {len(downstream)}. Linii amonte: {len(upstream)}."
        )
    upstream_with_receipts = sum(1 for line in upstream if line.receipt_summary != MISSING)
    upstream_with_stock = sum(1 for line in upstream if line.stock_at_moment != MISSING)
    return f"Pentru {exercise.code} / {exercise.lot}, raportul audit conține {len(production_orders)} comandă/comenzi de producție, {len(downstream)} livrare/livrări aval și {len(upstream)} linie/linii amonte. Recepții WMS mapate: {upstream_with_receipts}. Stocuri mapate: {upstream_with_stock}. Status bilanț: {balance.balance_status}."


def is_incomplete_finished_product_case(traceability_case: TraceabilityCase) -> bool:
    if traceability_case.subject.case_type != "FINISHED_PRODUCT":
        return False
    return not (
        has_finished_product_production_evidence(traceability_case)
        and has_finished_product_wms_production_out(traceability_case)
        and has_finished_product_upstream_evidence(traceability_case)
    )


def has_finished_product_production_evidence(traceability_case: TraceabilityCase) -> bool:
    return bool(
        traceability_case.report_tables.production.rows
        or (
            traceability_case.report_tables.order_traceability is not None
            and traceability_case.report_tables.order_traceability.rows
        )
    )


def has_finished_product_wms_production_out(traceability_case: TraceabilityCase) -> bool:
    order_table = traceability_case.report_tables.order_traceability
    if order_table is None:
        return False
    return any(value(row, "WMS production-out") != MISSING for row in order_table.rows)


def has_finished_product_upstream_evidence(traceability_case: TraceabilityCase) -> bool:
    return bool(
        traceability_case.report_tables.raw_materials.rows
        or traceability_case.report_tables.packaging.rows
        or traceability_case.report_tables.auxiliaries_gas.rows
    )


def detect_report_status(traceability_case: TraceabilityCase) -> str:
    if traceability_case.subject.case_type == "UNKNOWN":
        return STATUS_INCOMPLETE
    if is_incomplete_finished_product_case(traceability_case):
        return STATUS_INCOMPLETE
    if not traceability_case.report_tables.production.rows and not traceability_case.report_tables.finished_goods_deliveries.rows:
        return STATUS_INCOMPLETE
    if traceability_case.observations:
        return STATUS_PASS_WITH_OBSERVATIONS
    return STATUS_PASS


def detect_product_name(traceability_case: TraceabilityCase) -> str:
    for row in traceability_case.report_tables.production.rows:
        for key in ("Denumire", "Denumire produs"):
            found = value(row, key)
            if found != MISSING:
                return found
    order_table = traceability_case.report_tables.order_traceability
    if order_table:
        for row in order_table.rows:
            found = value(row, "Produs finit")
            if found != MISSING:
                return found
    return MISSING


def format_sources(traceability_case: TraceabilityCase) -> list[str]:
    sources: set[str] = set()
    for item in traceability_case.evidence:
        if item.source_key:
            sources.add(item.source_key)
    for table in (traceability_case.report_tables.production, traceability_case.report_tables.finished_goods_deliveries, traceability_case.report_tables.raw_materials, traceability_case.report_tables.packaging, traceability_case.report_tables.auxiliaries_gas, traceability_case.report_tables.wms_receipts, traceability_case.report_tables.stock, traceability_case.report_tables.order_traceability):
        if table is None:
            continue
        for row in table.rows:
            if row.source_key:
                sources.add(row.source_key)
    return sorted(sources)


def category_from_order_label(label: str) -> str:
    if label == "Materie primă alimentară":
        return "raw_material"
    if label == "Ambalaj":
        return "packaging"
    if label == "Auxiliar / gaz":
        return "auxiliary_gas"
    return "unknown"


def normalize_third_party_status(details: str) -> str:
    text = details.strip().casefold()
    if not text or text == "fara date identificate":
        return THIRD_PARTY_UNKNOWN
    if "nu se aplic" in text:
        return THIRD_PARTY_NOT_APPLICABLE
    if text == "nu" or text.startswith("nu "):
        return THIRD_PARTY_NO
    if text.startswith("da"):
        return THIRD_PARTY_YES
    return THIRD_PARTY_UNKNOWN


def merge_third_party_status(statuses: Iterable[str]) -> str:
    status_set = {status for status in statuses if status}
    if not status_set:
        return THIRD_PARTY_UNKNOWN
    if THIRD_PARTY_YES in status_set:
        return THIRD_PARTY_YES
    if status_set == {THIRD_PARTY_NO}:
        return THIRD_PARTY_NO
    if status_set == {THIRD_PARTY_NOT_APPLICABLE}:
        return THIRD_PARTY_NOT_APPLICABLE
    if status_set <= {THIRD_PARTY_NO, THIRD_PARTY_NOT_APPLICABLE}:
        return THIRD_PARTY_NO
    return THIRD_PARTY_UNKNOWN


def merge_third_party_details(status: str, details: list[str]) -> str:
    meaningful = dedupe([detail for detail in details if detail and detail != MISSING])
    if status == THIRD_PARTY_NOT_APPLICABLE:
        return "Nu se aplică"
    if status == THIRD_PARTY_NO:
        return "NU"
    if status == THIRD_PARTY_YES:
        return "; ".join(meaningful) if meaningful else "DA"
    return "; ".join(meaningful) if meaningful else MISSING


def merge_text_summaries(values: Iterable[str]) -> str:
    meaningful = dedupe([value_text.strip() for value_text in values if value_text and value_text.strip() and value_text.strip() != MISSING])
    if not meaningful:
        return MISSING
    return "; ".join(meaningful)


def format_stock_summary(stock_at_moment: str, stock_um: str) -> str:
    if not stock_at_moment or stock_at_moment == MISSING:
        return MISSING
    if not stock_um or stock_um == MISSING:
        return stock_at_moment
    if stock_at_moment.endswith(stock_um):
        return stock_at_moment
    return f"{stock_at_moment} {stock_um}"


def sum_by_unit(values: Any) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for quantity, unit in values:
        parsed = parse_decimal(quantity)
        unit_text = str(unit).strip()
        if parsed is None or not unit_text or unit_text == MISSING:
            continue
        totals[unit_text] = totals.get(unit_text, Decimal("0")) + parsed
    return totals


def single_total_or_missing(totals: dict[str, Decimal]) -> tuple[str, str]:
    if not totals:
        return MISSING, MISSING
    if len(totals) == 1:
        unit, quantity = next(iter(totals.items()))
        return format_decimal(quantity), unit
    return "; ".join(f"{format_decimal(quantity)} {unit}" for unit, quantity in sorted(totals.items())), "MIXT"


def split_quantity_unit(value_text: str) -> tuple[str, str]:
    if value_text == MISSING:
        return value_text, value_text
    parts = value_text.rsplit(" ", 1)
    if len(parts) != 2:
        return value_text, MISSING
    return parts[0], parts[1]


def quantities_equal(left: str, right: str) -> bool:
    left_decimal = parse_decimal(left)
    right_decimal = parse_decimal(right)
    if left_decimal is None or right_decimal is None:
        return False
    return abs(left_decimal - right_decimal) <= Decimal("0.000001")


def first_existing_value(row: TraceabilityTableRow, *keys: str) -> str:
    for key in keys:
        found = value(row, key)
        if found != MISSING:
            return found
    return MISSING


def value(row: TraceabilityTableRow, key: str) -> str:
    if key in row.values and str(row.values[key]).strip():
        return str(row.values[key]).strip()
    key_folded = key.casefold()
    for existing_key, existing_value in row.values.items():
        if existing_key.casefold() == key_folded and str(existing_value).strip():
            return str(existing_value).strip()
    normalized_key = normalize_key(key)
    for existing_key, existing_value in row.values.items():
        if normalize_key(existing_key) == normalized_key and str(existing_value).strip():
            return str(existing_value).strip()
    return MISSING


def normalize_key(value_text: object) -> str:
    text = str(value_text).casefold().strip()
    text = text.translate(str.maketrans({"ă": "a", "â": "a", "î": "i", "ș": "s", "ş": "s", "ț": "t", "ţ": "t"}))
    return "_".join(part for part in "".join(ch if ch.isalnum() else " " for ch in text).split())


def format_source(row: TraceabilityTableRow) -> str:
    parts = [row.source_key, row.source_name, row.sheet_name, str(row.row_number) if row.row_number is not None else None]
    return " / ".join(part for part in parts if part)


def parse_decimal(value_text: object) -> Decimal | None:
    text = str(value_text).strip().replace(" ", "")
    if not text or text == "FARADATEIDENTIFICATE":
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


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value_text in values:
        if not value_text or value_text in seen:
            continue
        seen.add(value_text)
        result.append(value_text)
    return result


def audit_traceability_report_to_dict(report: AuditTraceabilityReport) -> dict[str, Any]:
    return asdict(report)
