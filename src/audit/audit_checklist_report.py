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
    receipt_date_value,
    receipt_received_quantity,
    receipt_supplier_value,
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
    data_quality: dict[str, Any] = field(default_factory=dict)


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
        ChecklistDocumentRegisterLine(document.document_area, document.document_type, document.document_reference, document.related_code, document.related_lot, document.related_order, document.why_needed, document.status)
        for document in report.physical_documents
    ]
    exercise = ChecklistExercise(report.exercise.code, report.exercise.lot, report.exercise.product_name, report.exercise.case_type, report.exercise.traceability_result, report.exercise.data_sources, balance.observation)
    return AuditChecklistReport(
        conformity=build_conformity_items(balance, downstream, upstream, production_consumption, lot_flows, document_register, report.data_quality),
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
        data_quality=dict(report.data_quality),
    )


def map_downstream_delivery(delivery: FinishedProductDelivery) -> ChecklistDownstreamDelivery:
    client, address = split_client_and_address(delivery.client)
    return ChecklistDownstreamDelivery(client, address, delivery.delivery_date, join_quantity(delivery.quantity, delivery.um), "WMS document livrare", delivery.document_number, delivery.order_number, "Document livrare preluat din WMS.")


def map_upstream_line(line: UpstreamMaterialLine) -> ChecklistUpstreamLine:
    receipt = parse_receipt_summary(line.document_summary)
    checklist_line = ChecklistUpstreamLine(
        display_category(line.category),
        line.code,
        line.lot,
        line.name,
        join_quantity(line.quantity_consumed, line.um),
        receipt_date_value(line) if receipt_date_value(line) != MISSING else receipt["receipt_date"],
        receipt_supplier_value(line) if receipt_supplier_value(line) != MISSING else receipt["supplier"],
        receipt["document_type"],
        receipt["document_number"],
        receipt["document_date"],
        line.stock_at_moment,
        display_third_party_status(line.third_party_delivery_status),
        "; ".join(line.observations) if line.observations else "OK",
    )
    object.__setattr__(checklist_line, "_receipt_received_quantity", receipt_received_quantity(line))
    return checklist_line


def checklist_received_quantity(line: ChecklistUpstreamLine) -> str:
    return getattr(line, "_receipt_received_quantity", MISSING)


def build_production_consumption(report: AuditTraceabilityReport) -> list[ChecklistProductionConsumption]:
    rows: list[ChecklistProductionConsumption] = []
    for order in report.production_orders:
        production_date = getattr(order, "production_date", MISSING) or MISSING
        for line in [*order.raw_materials, *order.packaging, *order.auxiliaries_gas]:
            rows.append(
                ChecklistProductionConsumption(
                    production_order=order.production_order,
                    production_date=production_date,
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


def build_conformity_items(balance: ChecklistFinishedProductBalance, downstream: list[ChecklistDownstreamDelivery], upstream: list[ChecklistUpstreamLine], production_consumption: list[ChecklistProductionConsumption], lot_flows: list[ChecklistLotFlow], document_register: list[ChecklistDocumentRegisterLine], data_quality: dict[str, Any] | None = None) -> list[ChecklistConformityItem]:
    items = [
        ChecklistConformityItem("00_DATA_QUALITY — verificare surse înainte de raport", data_quality_status_for_checklist(data_quality), data_quality_evidence(data_quality), data_quality_observation(data_quality)),
        ChecklistConformityItem("01_EXERCITIU — fișa principală și bilanț produs finit", "DA" if balance.status != MISSING else "NU", f"PRD={balance.prd_produced}; WMS production-out={balance.wms_production_out}; WMS livrat={balance.wms_delivered}", balance.observation),
        ChecklistConformityItem("02_TABEL_I_AMONTE — materii prime, ambalaje, auxiliare/gaz", "DA" if upstream else "NU", f"{len(upstream)} linie/linii amonte", "Include lot, consum, recepție/furnizor/document/stoc unde există în surse."),
        ChecklistConformityItem("03_TABEL_II_AVAL — livrări produs finit", "DA" if downstream else "NU", f"{len(downstream)} livrare/livrări aval", "Include client, document WMS, cantitate și dată/adresă dacă există în sursă."),
        ChecklistConformityItem("04_PRODUCTIE_CONSUM — detaliere pe comenzi de producție", "DA" if production_consumption else "NU", f"{len(production_consumption)} rând(uri) consum pe comenzi", "Comenzile sunt separate de tabelul amonte agregat."),
        ChecklistConformityItem("05_FLUX_LOTURI_SI_DOCUMENTE — fluxuri și registru documente", "DA" if lot_flows and document_register else "NU", f"{len(lot_flows)} flux(uri), {len(document_register)} document(e) în registru", "Registrul documentelor fizice este generat pentru pregătirea auditului."),
    ]
    return items


def data_quality_status_for_checklist(data_quality: dict[str, Any] | None) -> str:
    status = str((data_quality or {}).get("status", "NOT_AVAILABLE"))
    if status == "OK":
        return "DA"
    if status == "WARNING":
        return "DA_CU_OBSERVATII"
    if status == "ERROR":
        return "NU"
    return "NECLAR"


def data_quality_evidence(data_quality: dict[str, Any] | None) -> str:
    summary = data_quality or {}
    return (
        f"Status={summary.get('status', 'NOT_AVAILABLE')}; "
        f"surse={summary.get('sources_found', 0)}/{summary.get('source_count', 0)}; "
        f"erori={summary.get('error_count', 0)}; "
        f"warning={summary.get('warning_count', 0)}; "
        f"issues={summary.get('issue_count', 0)}"
    )


def data_quality_observation(data_quality: dict[str, Any] | None) -> str:
    status = str((data_quality or {}).get("status", "NOT_AVAILABLE"))
    if status == "OK":
        return "Sursele obligatorii au trecut verificarea Data Quality inițială."
    if status == "WARNING":
        return "Raportul poate fi citit, dar există observații Data Quality de verificat."
    if status == "ERROR":
        return "Există erori Data Quality; verifică sursele înainte de concluzia finală."
    return "Sumarul Data Quality nu este disponibil pentru acest raport."


def parse_receipt_summary(summary: str) -> dict[str, str]:
    if not summary or summary == MISSING:
        return empty_receipt_fields()
    first_example = summary.split(";", 1)[1].strip() if ";" in summary else summary.strip()
    first_example = first_example.split(";", 1)[0].strip()
    document = first_example.rsplit(": ", 1)[0].strip() if ": " in first_example else first_example
    document = document.replace(" | data ", "/")
    detected_date = first_date([document])
    document_without_date = document.replace(detected_date, "").strip(" /") if detected_date != MISSING else document
    parts = [part.strip() for part in document_without_date.split("/") if part.strip()]
    document_number = parts[0] if parts else MISSING
    supplier = parts[1] if len(parts) >= 2 else MISSING
    return {"receipt_date": detected_date, "supplier": supplier or MISSING, "document_type": "WMS recepție", "document_number": document_number or MISSING, "document_date": detected_date}


def first_date(values: list[str]) -> str:
    for value_text in values:
        match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b", value_text)
        if match:
            return match.group(0)
    return MISSING


def empty_receipt_fields() -> dict[str, str]:
    return {"receipt_date": MISSING, "supplier": MISSING, "document_type": MISSING, "document_number": MISSING, "document_date": MISSING}


def split_client_and_address(client: str) -> tuple[str, str]:
    if not client or client == MISSING:
        return MISSING, MISSING
    text = client.strip()
    for separator in ["_-", " - ", "_", "-"]:
        if separator in text:
            left, right = text.split(separator, 1)
            left = left.strip(" _-")
            right = right.strip(" _-")
            if right:
                return left or text, right
    return text, MISSING


def parse_client_address(client: str) -> str:
    return split_client_and_address(client)[1]


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
    return {"raw_material": "Materie primă", "packaging": "Ambalaj", "auxiliary_gas": "Material auxiliar / gaz"}.get(category, category)


def display_third_party_status(status: str) -> str:
    return {"NU_SE_APLICA": "Nu se aplică", "NU": "NU", "DA": "DA", "NECLAR": "NECLAR"}.get(status, status or MISSING)


def audit_checklist_report_to_dict(report: AuditChecklistReport) -> dict[str, Any]:
    return asdict(report)
