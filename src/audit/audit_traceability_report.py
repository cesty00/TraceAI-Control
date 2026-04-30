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
from typing import Any

from src.rules.traceability_case import TraceabilityCase, TraceabilityReportTable, TraceabilityTableRow

STATUS_PASS = "PASS"
STATUS_PASS_WITH_OBSERVATIONS = "PASS_WITH_OBSERVATIONS"
STATUS_INCOMPLETE = "INCOMPLETE"
STATUS_FAIL = "FAIL"

THIRD_PARTY_NO = "NU"
THIRD_PARTY_YES = "DA"
THIRD_PARTY_UNKNOWN = "NECLAR"
THIRD_PARTY_NOT_APPLICABLE = "NU_SE_APLICA"


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


def build_audit_traceability_report(traceability_case: TraceabilityCase) -> AuditTraceabilityReport:
    """Build the audit DTO from a TraceabilityCase.

    This first implementation consumes the stable report_tables already produced
    by the rules layer. It does not re-read source files and does not invent
    unavailable document data.
    """

    exercise = AuditExercise(
        code=traceability_case.subject.code,
        lot=traceability_case.subject.lot,
        product_name=detect_product_name(traceability_case),
        case_type=traceability_case.subject.case_type,
        data_sources=format_sources(traceability_case),
        traceability_result=detect_report_status(traceability_case),
    )
    downstream = build_downstream(traceability_case.report_tables.finished_goods_deliveries)
    upstream = build_upstream(traceability_case)
    production_orders = build_production_orders(traceability_case, upstream)
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
    )


def build_downstream(table: TraceabilityReportTable) -> list[FinishedProductDelivery]:
    deliveries: list[FinishedProductDelivery] = []
    for row in table.rows:
        deliveries.append(
            FinishedProductDelivery(
                order_number=value(row, "Numar comanda"),
                document_number=value(row, "Document comanda"),
                client=value(row, "Client"),
                delivery_date="FARA DATE IDENTIFICATE",
                quantity=value(row, "Cantitate"),
                um=value(row, "UM"),
                rows="1",
                source_rows=[format_source(row)],
            )
        )
    return deliveries


def build_upstream(traceability_case: TraceabilityCase) -> list[UpstreamMaterialLine]:
    rows: list[UpstreamMaterialLine] = []
    rows.extend(upstream_from_table(traceability_case.report_tables.raw_materials, "raw_material", include_third_party=True))
    rows.extend(upstream_from_table(traceability_case.report_tables.packaging, "packaging", include_third_party=False))
    rows.extend(upstream_from_table(traceability_case.report_tables.auxiliaries_gas, "auxiliary_gas", include_third_party=False))
    return rows


def upstream_from_table(table: TraceabilityReportTable, category: str, include_third_party: bool) -> list[UpstreamMaterialLine]:
    lines: list[UpstreamMaterialLine] = []
    for row in table.rows:
        observations: list[str] = []
        third_party_status = THIRD_PARTY_UNKNOWN if include_third_party else THIRD_PARTY_NOT_APPLICABLE
        third_party_details = "FARA DATE IDENTIFICATE" if include_third_party else "Nu se aplică"
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
                receipt_summary="FARA DATE IDENTIFICATE",
                supplier_summary="FARA DATE IDENTIFICATE",
                document_summary="FARA DATE IDENTIFICATE",
                third_party_delivery_status=third_party_status,
                third_party_delivery_details=third_party_details,
                stock_at_moment="FARA DATE IDENTIFICATE",
                stock_um="FARA DATE IDENTIFICATE",
                observations=observations,
            )
        )
    return lines


def build_production_orders(traceability_case: TraceabilityCase, upstream: list[UpstreamMaterialLine]) -> list[ProductionOrderTrace]:
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
                wms_production_out_quantity="FARA DATE IDENTIFICATE",
                wms_production_out_um="FARA DATE IDENTIFICATE",
                associated_delivery="FARA DATE IDENTIFICATE",
                observations=["Detalierea pe comenzi nu este disponibilă în TraceabilityCase."],
            )
        )
    return result


def upstream_line_from_order_row(row: TraceabilityTableRow) -> UpstreamMaterialLine:
    third_party_details = value(row, "Livrări consum către terți")
    third_party_status = normalize_third_party_status(third_party_details)
    category = category_from_order_label(value(row, "Categorie consum"))
    return UpstreamMaterialLine(
        category=category,
        code=value(row, "Cod consum"),
        lot=value(row, "Lot consum"),
        name=value(row, "Denumire consum"),
        quantity_consumed=value(row, "Cantitate consum"),
        um=value(row, "UM consum"),
        receipt_summary="FARA DATE IDENTIFICATE",
        supplier_summary="FARA DATE IDENTIFICATE",
        document_summary="FARA DATE IDENTIFICATE",
        third_party_delivery_status=third_party_status,
        third_party_delivery_details=third_party_details,
        stock_at_moment="FARA DATE IDENTIFICATE",
        stock_um="FARA DATE IDENTIFICATE",
        observations=[] if third_party_status != THIRD_PARTY_UNKNOWN else ["Status livrări către terți neclar în datele disponibile."],
    )


def build_finished_product_balance(
    traceability_case: TraceabilityCase,
    downstream: list[FinishedProductDelivery],
    production_orders: list[ProductionOrderTrace],
) -> FinishedProductBalance:
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
    if prd_quantity != "FARA DATE IDENTIFICATE" and out_quantity != "FARA DATE IDENTIFICATE":
        if quantities_equal(prd_quantity, out_quantity) and prd_um == out_um:
            status = STATUS_PASS
            observations.append("PRD produs coincide cu WMS PRODUCTION-OUT.")
        else:
            status = STATUS_PASS_WITH_OBSERVATIONS
            observations.append("PRD produs diferă de WMS PRODUCTION-OUT; verificare manuală necesară.")
    if delivered_quantity != "FARA DATE IDENTIFICATE":
        observations.append("Livrările sunt preluate din WMS și se evaluează în valoare absolută pentru reconciliere.")
    return FinishedProductBalance(
        prd_produced_quantity=prd_quantity,
        prd_produced_um=prd_um,
        wms_production_out_quantity=out_quantity,
        wms_production_out_um=out_um,
        wms_delivered_quantity=delivered_quantity,
        wms_delivered_um=delivered_um,
        stock_quantity=stock_quantity,
        stock_um=stock_um,
        adjustments_quantity="FARA DATE IDENTIFICATE",
        adjustments_um="FARA DATE IDENTIFICATE",
        balance_status=status,
        balance_observation=" ".join(observations) if observations else "FARA DATE IDENTIFICATE",
    )


def build_source_lot_flows(upstream: list[UpstreamMaterialLine]) -> list[SourceLotFlow]:
    flows: list[SourceLotFlow] = []
    for line in upstream:
        flows.append(
            SourceLotFlow(
                category=line.category,
                code=line.code,
                lot=line.lot,
                name=line.name,
                receipt_total=line.receipt_summary,
                receipt_documents=line.document_summary,
                consumed_in_audited_lot=f"{line.quantity_consumed} {line.um}",
                consumed_in_other_orders="FARA DATE IDENTIFICATE",
                third_party_delivered_total=line.third_party_delivery_details,
                adjustments_total="FARA DATE IDENTIFICATE",
                stock_at_moment=f"{line.stock_at_moment} {line.stock_um}" if line.stock_at_moment != "FARA DATE IDENTIFICATE" else "FARA DATE IDENTIFICATE",
                flow_status="documentat parțial" if line.receipt_summary == "FARA DATE IDENTIFICATE" else "documentat",
                observation="; ".join(line.observations) if line.observations else "FARA DATE IDENTIFICATE",
            )
        )
    return flows


def build_physical_document_requirements(
    exercise: AuditExercise,
    downstream: list[FinishedProductDelivery],
    upstream: list[UpstreamMaterialLine],
    production_orders: list[ProductionOrderTrace],
) -> list[PhysicalDocumentRequirement]:
    documents: list[PhysicalDocumentRequirement] = []
    for order in production_orders:
        documents.append(
            PhysicalDocumentRequirement(
                document_area="PRD",
                document_type="Comandă / raport producție",
                document_reference=order.production_order,
                related_code=exercise.code,
                related_lot=exercise.lot,
                related_order=order.production_order,
                why_needed="Confirmă producția și consumurile pe comandă.",
                status="required",
            )
        )
    for delivery in downstream:
        documents.append(
            PhysicalDocumentRequirement(
                document_area="WMS",
                document_type="Document livrare produs finit",
                document_reference=delivery.document_number,
                related_code=exercise.code,
                related_lot=exercise.lot,
                related_order=delivery.order_number,
                why_needed="Confirmă livrarea aval către client.",
                status="required",
            )
        )
    for line in upstream:
        documents.append(
            PhysicalDocumentRequirement(
                document_area="NIR" if line.category == "raw_material" else "WMS",
                document_type="Document intrare / recepție lot sursă",
                document_reference=line.document_summary,
                related_code=line.code,
                related_lot=line.lot,
                related_order="FARA DATE IDENTIFICATE",
                why_needed="Confirmă intrarea lotului sursă folosit în lotul auditat.",
                status="required" if line.category in {"raw_material", "packaging"} else "recommended",
            )
        )
    return documents


def collect_observations(
    traceability_case: TraceabilityCase,
    upstream: list[UpstreamMaterialLine],
    production_orders: list[ProductionOrderTrace],
    balance: FinishedProductBalance,
) -> list[str]:
    observations = list(traceability_case.observations)
    if balance.balance_observation != "FARA DATE IDENTIFICATE":
        observations.append(balance.balance_observation)
    if any(line.third_party_delivery_status == THIRD_PARTY_NO for line in upstream if line.category == "raw_material"):
        observations.append("Pentru cel puțin un lot de materie primă nu au fost identificate livrări către terți.")
    if any(not order.associated_delivery or order.associated_delivery == "FARA DATE IDENTIFICATE" for order in production_orders):
        observations.append("Unele comenzi nu au livrare produs finit asociată explicit în TraceabilityCase.")
    return dedupe(observations)


def build_conclusion_summary(
    exercise: AuditExercise,
    balance: FinishedProductBalance,
    downstream: list[FinishedProductDelivery],
    upstream: list[UpstreamMaterialLine],
    production_orders: list[ProductionOrderTrace],
) -> str:
    return (
        f"Pentru {exercise.code} / {exercise.lot}, raportul audit conține "
        f"{len(production_orders)} comandă/comenzi de producție, {len(downstream)} livrare/livrări aval "
        f"și {len(upstream)} linie/linii amonte. Status bilanț: {balance.balance_status}."
    )


def detect_report_status(traceability_case: TraceabilityCase) -> str:
    if traceability_case.subject.case_type == "UNKNOWN":
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
            if found != "FARA DATE IDENTIFICATE":
                return found
    order_table = traceability_case.report_tables.order_traceability
    if order_table:
        for row in order_table.rows:
            found = value(row, "Produs finit")
            if found != "FARA DATE IDENTIFICATE":
                return found
    return "FARA DATE IDENTIFICATE"


def format_sources(traceability_case: TraceabilityCase) -> list[str]:
    sources: set[str] = set()
    for item in traceability_case.evidence:
        if item.source_key:
            sources.add(item.source_key)
    for table in (
        traceability_case.report_tables.production,
        traceability_case.report_tables.finished_goods_deliveries,
        traceability_case.report_tables.raw_materials,
        traceability_case.report_tables.packaging,
        traceability_case.report_tables.auxiliaries_gas,
        traceability_case.report_tables.wms_receipts,
        traceability_case.report_tables.stock,
        traceability_case.report_tables.order_traceability,
    ):
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


def sum_by_unit(values: Any) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for quantity, unit in values:
        parsed = parse_decimal(quantity)
        unit_text = str(unit).strip()
        if parsed is None or not unit_text or unit_text == "FARA DATE IDENTIFICATE":
            continue
        totals[unit_text] = totals.get(unit_text, Decimal("0")) + parsed
    return totals


def single_total_or_missing(totals: dict[str, Decimal]) -> tuple[str, str]:
    if not totals:
        return "FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE"
    if len(totals) == 1:
        unit, quantity = next(iter(totals.items()))
        return format_decimal(quantity), unit
    return "; ".join(f"{format_decimal(quantity)} {unit}" for unit, quantity in sorted(totals.items())), "MIXT"


def split_quantity_unit(value_text: str) -> tuple[str, str]:
    if value_text == "FARA DATE IDENTIFICATE":
        return value_text, value_text
    parts = value_text.rsplit(" ", 1)
    if len(parts) != 2:
        return value_text, "FARA DATE IDENTIFICATE"
    return parts[0], parts[1]


def quantities_equal(left: str, right: str) -> bool:
    left_decimal = parse_decimal(left)
    right_decimal = parse_decimal(right)
    if left_decimal is None or right_decimal is None:
        return False
    return abs(left_decimal - right_decimal) <= Decimal("0.000001")


def value(row: TraceabilityTableRow, key: str) -> str:
    if key in row.values and str(row.values[key]).strip():
        return str(row.values[key]).strip()
    key_folded = key.casefold()
    for existing_key, existing_value in row.values.items():
        if existing_key.casefold() == key_folded and str(existing_value).strip():
            return str(existing_value).strip()
    return "FARA DATE IDENTIFICATE"


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
