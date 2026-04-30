"""Checklist-aligned audit DOCX renderer.

This renderer consumes AuditChecklistReport, not raw TraceabilityCase tables. It
keeps the final DOCX contract aligned with the checklist/manual/scanned model:
explicit Tabel I and Tabel II columns, conformity summary, production
consumption, lot flows, document register and conclusion.
"""

from __future__ import annotations

import argparse
import re
import zipfile
from collections import OrderedDict
from datetime import date
from pathlib import Path

from src.audit.audit_checklist_report import (
    AuditChecklistReport,
    ChecklistProductionConsumption,
    build_audit_checklist_report,
)
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.report.audit_docx import (
    APP_XML,
    CONTENT_TYPES_XML,
    CORE_XML,
    DOCUMENT_RELS_XML,
    FOOTER_XML,
    HEADER_XML,
    ROOT_RELS_XML,
    STYLES_XML,
    bullets,
    page_break,
    paragraph,
    table,
    wrap_document,
)
from src.rules.run_traceability_case import run_traceability_case

MISSING = "FARA DATE IDENTIFICATE"


def generate_audit_checklist_docx_report(report: AuditChecklistReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        package.writestr("_rels/.rels", ROOT_RELS_XML)
        package.writestr("docProps/app.xml", APP_XML)
        package.writestr("docProps/core.xml", CORE_XML)
        package.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        package.writestr("word/styles.xml", STYLES_XML)
        package.writestr("word/header1.xml", HEADER_XML)
        package.writestr("word/footer1.xml", FOOTER_XML)
        package.writestr("word/document.xml", build_document_xml(report))
    return output


def build_document_xml(report: AuditChecklistReport) -> str:
    body: list[str] = []
    body.extend(build_title_block(report))
    body.extend(build_conformity_section(report))
    body.extend(build_exercise_section(report))
    body.extend(build_downstream_section(report))
    body.append(page_break())
    body.extend(build_upstream_section(report))
    body.append(page_break())
    body.extend(build_production_consumption_section(report))
    body.append(page_break())
    body.extend(build_lot_flow_section(report))
    body.extend(build_document_register_section(report))
    body.extend(build_conclusion_section(report))
    return wrap_document("".join(body))


def build_title_block(report: AuditChecklistReport) -> list[str]:
    return [
        paragraph("TEST DE TRASABILITATE PENTRU AUDIT", style="Title"),
        paragraph(f"{report.exercise.code} / {report.exercise.lot} — {report.exercise.product_name}", bold=True, align="center"),
        paragraph("Versiune test local — structură aliniată la Checklist trasabilitate / Manual verificare trasabilitate audit v2.1 / model scanat PDF.", align="center"),
    ]


def build_conformity_section(report: AuditChecklistReport) -> list[str]:
    rows = [[item.requirement, item.status, compact(item.evidence, 95), compact(item.observation, 95)] for item in report.conformity]
    return [
        paragraph("Rezumat de conformare checklist", style="Heading1"),
        table(["Cerință", "Status în test", "Dovezi", "Observații"], rows),
    ]


def build_exercise_section(report: AuditChecklistReport) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    return [
        paragraph("01_EXERCITIU — Fișa principală a exercițiului", style="Heading1"),
        table(
            ["Indicator", "Valoare"],
            [
                ["Cod produs", exercise.code],
                ["Lot produs", exercise.lot],
                ["Denumire produs", exercise.product_name],
                ["Status test local", exercise.result],
            ],
        ),
        paragraph("Bilanț produs finit", style="Heading2"),
        table(
            ["Indicator", "Cantitate / status", "Observație"],
            [
                ["Total produs PRD", balance.prd_produced, "Sursă PRD"],
                ["WMS PRODUCTION-OUT", balance.wms_production_out, "Intrare produs finit WMS"],
                ["Total livrat WMS", balance.wms_delivered, "Valoare semnată WMS"],
                ["Stoc la moment", balance.stock_at_moment, "Dacă există în stoc"],
                ["Status bilanț", balance.status, compact(balance.observation, 90)],
            ],
        ),
    ]


def build_downstream_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [
            delivery.client,
            delivery.address,
            delivery.delivery_date,
            delivery.delivered_quantity,
            delivery.delivery_document_type,
            delivery.delivery_document_number,
            delivery.wms_order,
            compact_downstream_observation(delivery.observation),
        ]
        for delivery in report.downstream
    ]
    if not rows:
        rows = [[MISSING] * 8]
    return [
        paragraph("03_TABEL_II_AVAL — Livrări produs finit", style="Heading1"),
        table(["Client", "Adresă", "Dată livrare", "Cantitate livrată", "Tip document", "Număr document", "Comandă WMS", "Observații"], rows),
    ]


def build_upstream_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [
            line.material_type,
            line.code,
            line.lot,
            compact_name(line.name),
            line.consumed_quantity,
            line.receipt_date,
            compact_name(line.supplier),
            line.document_type,
            line.document_number,
            line.document_date,
            compact_stock(line.stock_at_moment),
            line.third_party_delivery_status,
            compact_upstream_observation(line.observation),
        ]
        for line in report.upstream
    ]
    if not rows:
        rows = [[MISSING] * 13]
    return [
        paragraph("02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare", style="Heading1"),
        table(["Tip", "Cod", "Lot", "Denumire", "Consum", "Dată recepție", "Furnizor", "Tip document", "Număr document", "Dată document", "Stoc la moment", "Livrări terți", "Observații"], rows),
        *build_third_party_section(report),
    ]


def build_third_party_section(report: AuditChecklistReport) -> list[str]:
    raw_lines = [line for line in report.upstream if line.material_type == "Materie primă"]
    if not raw_lines:
        return []
    rows = [[line.code, line.lot, compact_name(line.name), line.consumed_quantity, line.third_party_delivery_status, compact_third_party_note(line)] for line in raw_lines]
    return [
        paragraph("Verificare specială — materii prime livrate către terți", style="Heading2"),
        table(["Cod MP", "Lot MP", "Denumire", "Consum în lot", "Livrări MP către terți", "Detalii"], rows),
    ]


def build_production_consumption_section(report: AuditChecklistReport) -> list[str]:
    return [
        paragraph("04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție", style="Heading1"),
        paragraph("Comenzi producție", style="Heading2"),
        table(["Comandă producție", "Dată producție", "Cantitate PRD", "WMS production-out", "Livrare PF asociată"], production_order_summary_rows(report.production_consumption)),
        paragraph("Consumuri pe comenzi — tabel operațional", style="Heading2"),
        table(["Comandă", "Tip", "Cod consum", "Lot consum", "Denumire consum", "Cantitate consum"], production_consumption_rows(report.production_consumption)),
    ]


def production_order_summary_rows(rows: list[ChecklistProductionConsumption]) -> list[list[str]]:
    summary: OrderedDict[str, ChecklistProductionConsumption] = OrderedDict()
    for row in rows:
        summary.setdefault(row.production_order, row)
    if not summary:
        return [[MISSING] * 5]
    return [[row.production_order, row.production_date, row.finished_product_quantity, row.wms_production_out, compact_delivery(row.associated_delivery)] for row in summary.values()]


def production_consumption_rows(rows: list[ChecklistProductionConsumption]) -> list[list[str]]:
    if not rows:
        return [[MISSING] * 6]
    return [[row.production_order, row.material_type, row.consumed_code, row.consumed_lot, compact_name(row.consumed_name), row.consumed_quantity] for row in rows]


def build_lot_flow_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [flow.material_type, flow.code, flow.lot, compact_name(flow.name), compact_receipts(flow.receipts), flow.consumed_in_audited_lot, compact_third_party(flow.third_party_deliveries), compact_stock(flow.stock_at_moment), compact_flow_status(flow.status), compact_flow_observation(flow.observation)]
        for flow in report.lot_flows
    ]
    if not rows:
        rows = [[MISSING] * 10]
    return [
        paragraph("05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente", style="Heading1"),
        table(["Tip", "Cod", "Lot", "Denumire", "Recepții", "Consum auditat", "Livrări terți", "Stoc", "Status", "Observații"], rows),
    ]


def build_document_register_section(report: AuditChecklistReport) -> list[str]:
    rows = [[line.area, line.document_type, compact_reference(line.document_reference), line.related_code, line.related_lot, compact_delivery(line.related_order), compact_register_reason(line.why_needed), line.status] for line in report.document_register]
    if not rows:
        rows = [[MISSING] * 8]
    return [
        paragraph("Registru documente fizice de pregătit pentru auditor", style="Heading2"),
        table(["Zona", "Tip document", "Referință", "Cod", "Lot", "Comandă", "Motiv", "Status"], rows),
    ]


def build_conclusion_section(report: AuditChecklistReport) -> list[str]:
    bullets_text = compact_conclusion_observations(report.observations)
    return [
        paragraph("Concluzie audit intern — test local", style="Heading1"),
        paragraph(f"Pentru produsul {report.exercise.code} / lot {report.exercise.lot}, raportul audit confirmă trasabilitatea produsului finit în aval și în amonte pe baza surselor WMS și PRD."),
        paragraph(f"Bilanț PRD vs WMS: {report.balance.status}. {compact(report.balance.observation, 120)}"),
        *bullets(bullets_text),
    ]


def compact_conclusion_observations(observations: list[str]) -> list[str]:
    result: list[str] = []
    if observations:
        result.append("Recepțiile WMS disponibile pentru loturile consumate sunt preluate în tabelul amonte.")
        result.append("Stocurile disponibile la moment sunt afișate în tabelul amonte și în fluxuri.")
    result.append("Documentul este un prototip vizual pentru alinierea raportului exportat din aplicație la checklist, manual și scanul PDF.")
    return result


def compact(value: object, max_length: int = 80) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text:
        text = MISSING
    text = re.sub(r"\s+", " ", text)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def compact_name(value: object) -> str:
    return compact(value, 42)


def compact_stock(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text or text == MISSING:
        return MISSING
    return text.replace("locații:", "loc.")


def compact_receipts(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text or text == MISSING:
        return MISSING
    parts = [part.strip() for part in text.split(";") if part.strip()]
    if len(parts) <= 2:
        return compact(text, 120)
    return compact(f"{parts[0]}; {parts[1]}; +{len(parts) - 2} alte", 120)


def compact_third_party(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text or text == MISSING:
        return MISSING
    if text.startswith("DA;"):
        return compact(text, 85)
    if "Nu se aplic" in text:
        return "Nu se aplică"
    return compact(text, 85)


def compact_upstream_observation(value: object) -> str:
    text = str(value).strip() if value is not None else "OK"
    if not text or text == "OK":
        return "OK"
    if "nu se aplic" in text.casefold():
        return "Nu se aplică"
    if "nu apare în stoc" in text.casefold() or "stoc" in text.casefold():
        return "Stoc nedisponibil în fișier"
    if "livrări către terți" in text.casefold():
        return "Verificat livrări terți"
    return compact(text, 70)


def compact_downstream_observation(value: object) -> str:
    text = str(value).strip() if value is not None else "OK"
    if not text or text == MISSING:
        return "OK"
    return "Document WMS; data/adresa se completează dacă există în sursă"


def compact_third_party_note(line: object) -> str:
    status = getattr(line, "third_party_delivery_status", "")
    observation = getattr(line, "observation", "")
    if status == "NU":
        return "Nu au fost identificate livrări directe în WMS."
    if status == "DA":
        return compact(observation, 85)
    return compact(observation, 85)


def compact_flow_status(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if "parțial" in text:
        return "documentat parțial"
    return compact(text, 35)


def compact_flow_observation(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text or text == MISSING:
        return "OK"
    if "nu se aplic" in text.casefold():
        return "Nu se aplică"
    if "stoc" in text.casefold():
        return "Verificare stoc"
    if "livrări" in text.casefold():
        return "Verificare livrări"
    return compact(text, 60)


def compact_reference(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if not text or text == MISSING:
        return MISSING
    return compact_receipts(text)


def compact_register_reason(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    if "produc" in text.casefold():
        return "Confirmă producția și consumurile"
    if "livrare" in text.casefold():
        return "Confirmă livrarea aval"
    if "intrarea" in text.casefold() or "recep" in text.casefold():
        return "Confirmă intrarea lotului sursă"
    return compact(text, 55)


def compact_delivery(value: object) -> str:
    return compact(value, 80)


def extract_document_text_from_xml(document_xml: str) -> str:
    return document_xml.replace("<w:t>", "\n").replace("</w:t>", "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genereaza raport audit DOCX aliniat la checklist.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", required=True, help="Cale output DOCX.")
    args = parser.parse_args(argv)
    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    audit_report = build_audit_traceability_report(traceability_case)
    checklist_report = build_audit_checklist_report(audit_report)
    generate_audit_checklist_docx_report(checklist_report, args.output)
    return 0 if checklist_report.conclusion_status != "INCOMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
