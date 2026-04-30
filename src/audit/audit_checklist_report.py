"""Checklist-level audit report model.

This module converts AuditTraceabilityReport into a report contract aligned with:
- Checklist-trasabilitate.pdf
- Manual_verificare_trasabilitate_audit_v2.1.docx
- the scanned audit report model validated visually by the user

The key difference from AuditTraceabilityReport is that checklist fields are
split into explicit columns. Renderers should use this model when producing the
final DOCX for audit, instead of parsing compact text summaries in templates.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from src.audit.audit_traceability_report import (
    MISSING,
    AuditTraceabilityReport,
    FinishedProductDelivery,
    UpstreamMaterialLine,
)


@dataclass(frozen=True)
class ChecklistConformityItem:
    requirement: str
    status: str
    evidence: str
    observation: str = ""


@dataclass(frozen=True)
class ChecklistExercise:
    code: str
    lot: str
    product_name: str
    case_type: str
    result: str
    generated_from_sources: list[str]
    balance_summary: str


@dataclass(frozen=True)
class ChecklistFinishedProductBalance:
    prd_produced: str
    wms_production_out: str
    wms_delivered: str
    stock_at_moment: str
    adjustments: str
    status: str
    observation: str


@dataclass(frozen=True)
class ChecklistDownstreamDelivery:
    client: str
    address: str
    delivery_date: str
    delivered_quantity: str
    delivery_document_type: str
    delivery_document_number: str
    wms_order: str
    observation: str = ""


@dataclass(frozen=True)
class ChecklistUpstreamLine:
    material_type: str
    code: str
    lot: str
    name: str
    consumed_quantity: str
    receipt_date: str
    supplier: str
    document_type: str
    document_number: str
    document_date: str
    stock_at_moment: str
    third_party_delivery_status: str
    observation: str = ""


@dataclass(frozen=True)
class ChecklistProductionConsumption:
    production_order: str
    production_date: str
    finished_product_quantity: str
    wms_production_out: str
    associated_delivery: str
    consumed_code: str
    consumed_lot: str
    consumed_name: str
    consumed_quantity: str
    material_type: str


@dataclass(frozen=True)
class ChecklistLotFlow:
    material_type: str
    code: str
    lot: str
    name: str
    receipts: str
    consumed_in_audited_lot: str
    third_party_deliveries: str
    stock_at_moment: str
    status: str
    observation: str


@dataclass(frozen=True)
class ChecklistDocumentRegisterLine:
    area: str
    document_type: str
    document_reference: str
    related_code: str
    related_lot: str
    related_order: str
    why_needed: str
    status: str


@dataclass(frozen=True)
class AuditChecklistReport:
    conformity: list[ChecklistConformityItem]
    exercise: ChecklistExercise
    balance: ChecklistFinishedProductBalance
    downstream: list[ChecklistDownstreamDelivery]
    upstream: list[ChecklistUpstreamLine]
    production_consumption: list[ChecklistProductionConsumption]
    lot_flows: list[ChecklistLotFlow]
    document_register: list[ChecklistDocumentRegisterLine]
    conclusion_status: str
    conclusion_text: str
    observations: list[str] = field(default_factory=list)


def build_audit_checklist_report(report: AuditTraceabilityReport) -> AuditChecklistReport:
    balance = ChecklistFinishedProductBalance(
        prd_produced=join_quantity(report.balance.prd_produced_quantity, report.balance.prd_produced_um),
        wms_production_out=join_quantity(report.balance.wms_production_out_quantity, report.balance.wms_production_out_um),
        wms_delivered=join_quantity(report.balance.wms_delivered_quantity, report.balance.wms_delivered_um),
        stock_at_moment=join_quantity(report.balance.stock_quantity, report.balance.stock_um),
        adjustments=join_quantity(report.balance.adjustments_quantity, report.balance.adjustments_um),
        status=report.balance.balance_status,
        observation=report.balance.balance_observation,
    )
    downstream = [map_downstream_delivery(delivery) for delivery in report.downstream]
    upstream = [map_upstream_line(line) for line in report.upstream]
    production_consumption = build_production_consumption(report)
    lot_flows = [
        ChecklistLotFlow(
            material_type=display_category(flow.category),
            code=flow.code,
            lot=flow.lot,
            name=flow.name,
            receipts=flow.receipt_total,
            consumed_in_audited_lot=flow.consumed_in_audited_lot,
            third_party_deliveries=flow.third_party_delivered_total,
            stock_at_moment=flow.stock_at_moment,
            status=flow.flow_status,
            observation=flow.observation,
        )
        for flow in report.source_lot_flows
    ]
    document_register = [
        ChecklistDocumentRegisterLine(
            area=document.document_area,
            document_type=document.document_type,
            document_reference=document.document_reference,
            related_code=document.related_code,
            related_lot=document.related_lot,
            related_order=document.related_order,
            why_needed=document.why_needed,
            status=document.status,
        )
        for document in report.physical_documents
    ]
    exercise = ChecklistExercise(
        code=report.exercise.code,
        lot=report.exercise.lot,
        product_name=report.exercise.product_name,
        case_type=report.exercise.case_type,
        result=report.exercise.traceability_result,
        generated_from_sources=report.exercise.data_sources,
        balance_summary=balance.observation,
    )
    return AuditChecklistReport(
        conformity=build_conformity_items(balance, downstream, upstream, production_consumption, lot_flows, document_register),
        exercise=exercise,
        balance=balance,
        downstream=downstream,
        upstream=upstream,
        production_consumption=production_consumption,
        lot_flows=lot_flows,
        document_register=document_register,
        conclusion_status=report.conclusion.status,
        conclusion_text=report.conclusion.summary,
        observations=report.conclusion.observations,
    )


def map_downstream_delivery(delivery: FinishedProductDelivery) -> ChecklistDownstreamDelivery:
    return ChecklistDownstreamDelivery(
        client=delivery.client,
        address=parse_client_address(delivery.client),
        delivery_date=delivery.delivery_date,
        delivered_quantity=join_quantity(delivery.quantity, delivery.um),
        delivery_document_type="WMS document livrare",
        delivery_document_number=delivery.document_number,
        wms_order=delivery.order_number,
        observation="Document livrare preluat din WMS; data/adresa se completează dacă există în sursă.",
    )


def map_upstream_line(line: UpstreamMaterialLine) -> ChecklistUpstreamLine:
    receipt = parse_receipt_summary(line.document_summary)
    return ChecklistUpstreamLine(
        material_type=display_category(line.category),
        code=line.code,
        lot=line.lot,
        name=line.name,
        consumed_quantity=join_quantity(line.quantity_consumed, line.um),
        receipt_date=receipt["receipt_date"],
        supplier=receipt["supplier"],
        document_type=receipt["document_type"],
        document_number=receipt["document_number"],
        document_date=receipt["document_date"],
        stock_at_moment=line.stock_at_moment,
        third_party_delivery_status=display_third_party_status(line.third_party_delivery_status),
        observation="; ".join(line.observations) if line.observations else "OK",
    )


def build_production_consumption(report: AuditTraceabilityReport) -> list[ChecklistProductionConsumption]:
    rows: list[ChecklistProductionConsumption] = []
    for order in report.production_orders:
        for line in [*order.raw_materials, *order.packaging, *order.auxiliaries_gas]:
            rows.append(
                ChecklistProductionConsumption(
                    production_order=order.production_order,
                    production_date=MISSING,
                    finished_product_quantity=join_quantity(order.prd_quantity, order.prd_um),
                    wms_production_out=join_quantity(order.wms_production_out_quantity, order.wms_production_out_um),
                    associated_delivery=order.associated_delivery,
                    consumed_code=line.code,
                    consumed_lot=line.lot,
                    consumed_name=line.name,
                    consumed_quantity=join_quantity(line.quantity_consumed, line.um),
                    material_type=display_category(line.category),
                )
            )
    return rows


def build_conformity_items(
    balance: ChecklistFinishedProductBalance,
    downstream: list[ChecklistDownstreamDelivery],
    upstream: list[ChecklistUpstreamLine],
    production_consumption: list[ChecklistProductionConsumption],
    lot_flows: list[ChecklistLotFlow],
    document_register: list[ChecklistDocumentRegisterLine],
) -> list[ChecklistConformityItem]:
    return [
        ChecklistConformityItem(
            requirement="01_EXERCITIU — fișa principală și bilanț produs finit",
            status="DA" if balance.status != MISSING else "NU",
            evidence=f"PRD={balance.prd_produced}; WMS production-out={balance.wms_production_out}; WMS livrat={balance.wms_delivered}",
            observation=balance.observation,
        ),
        ChecklistConformityItem(
            requirement="02_TABEL_I_AMONTE — materii prime, ambalaje, auxiliare/gaz",
            status="DA" if upstream else "NU",
            evidence=f"{len(upstream)} linie/linii amonte",
            observation="Include lot, consum, recepție/furnizor/document/stoc unde există în surse.",
        ),
        ChecklistConformityItem(
            requirement="03_TABEL_II_AVAL — livrări produs finit",
            status="DA" if downstream else "NU",
            evidence=f"{len(downstream)} livrare/livrări aval",
            observation="Include client, document WMS, cantitate și dată/adresă dacă există în sursă.",
        ),
        ChecklistConformityItem(
            requirement="04_PRODUCTIE_CONSUM — detaliere pe comenzi de producție",
            status="DA" if production_consumption else "NU",
            evidence=f"{len(production_consumption)} rând(uri) consum pe comenzi",
            observation="Comenzile sunt separate de tabelul amonte agregat.",
        ),
        ChecklistConformityItem(
            requirement="05_FLUX_LOTURI_SI_DOCUMENTE — fluxuri și registru documente",
            status="DA" if lot_flows and document_register else "NU",
            evidence=f"{len(lot_flows)} flux(uri), {len(document_register)} document(e) în registru",
            observation="Registrul documentelor fizice este generat pentru pregătirea auditului.",
        ),
    ]


def parse_receipt_summary(summary: str) -> dict[str, str]:
    if not summary or summary == MISSING:
        return empty_receipt_fields()
    first_example = summary.split(";", 1)[1].strip() if ";" in summary else summary.strip()
    first_example = first_example.split(";", 1)[0].strip()
    # Expected examples from WMS summaries look like:
    # 300005747/Fish Invest LTD: 5000 Kilogram
    # 7162847/DUNAPACK RAMBOX PRODIMPEX SRL: 4000 BUCATA
    document = first_example
    supplier = MISSING
    if ":" in document:
        document = document.split(":", 1)[0].strip()
    if "/" in document:
        document_number, supplier = document.split("/", 1)
    else:
        document_number = document
    return {
        "receipt_date": MISSING,
        "supplier": supplier.strip() or MISSING,
        "document_type": "WMS recepție",
        "document_number": document_number.strip() or MISSING,
        "document_date": MISSING,
    }


def empty_receipt_fields() -> dict[str, str]:
    return {
        "receipt_date": MISSING,
        "supplier": MISSING,
        "document_type": MISSING,
        "document_number": MISSING,
        "document_date": MISSING,
    }


def parse_client_address(client: str) -> str:
    if not client or client == MISSING:
        return MISSING
    if " - " in client:
        return client.split(" - ", 1)[1].strip() or MISSING
    return MISSING


def join_quantity(quantity: object, unit: object) -> str:
    quantity_text = str(quantity).strip() if quantity is not None else MISSING
    unit_text = str(unit).strip() if unit is not None else MISSING
    if not quantity_text:
        quantity_text = MISSING
    if not unit_text:
        unit_text = MISSING
    if quantity_text == MISSING and unit_text == MISSING:
        return MISSING
    if unit_text == MISSING:
        return quantity_text
    return f"{quantity_text} {unit_text}"


def display_category(category: str) -> str:
    return {
        "raw_material": "Materie primă",
        "packaging": "Ambalaj",
        "auxiliary_gas": "Material auxiliar / gaz",
    }.get(category, category)


def display_third_party_status(status: str) -> str:
    return {
        "NU_SE_APLICA": "Nu se aplică",
        "NU": "NU",
        "DA": "DA",
        "NECLAR": "NECLAR",
    }.get(status, status or MISSING)


def audit_checklist_report_to_dict(report: AuditChecklistReport) -> dict[str, Any]:
    return asdict(report)
