"""Checklist-aligned audit DOCX renderer.

This renderer consumes AuditChecklistReport, not raw TraceabilityCase tables. It
keeps the final DOCX contract aligned with the checklist/manual/scanned model:
explicit Tabel I and Tabel II columns, conformity summary, production
consumption, lot flows, document register and conclusion.
"""

from __future__ import annotations

import argparse
import zipfile
from datetime import date
from pathlib import Path
from typing import Iterable

from src.audit.audit_checklist_report import (
    AuditChecklistReport,
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
    escape,
    page_break,
    paragraph,
    table,
    value_or_missing,
    wrap_document,
)
from src.rules.run_traceability_case import run_traceability_case


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
    body.extend(build_sources_section(report))
    return wrap_document("".join(body))


def build_title_block(report: AuditChecklistReport) -> list[str]:
    return [
        paragraph("TEST DE TRASABILITATE PENTRU AUDIT", style="Title"),
        paragraph(f"{report.exercise.code} / {report.exercise.lot} — {report.exercise.product_name}", bold=True, align="center"),
        paragraph("Raport generat conform Checklist trasabilitate, Manual verificare trasabilitate audit v2.1 și modelului scanat validat vizual.", align="center"),
    ]


def build_conformity_section(report: AuditChecklistReport) -> list[str]:
    rows = [[item.requirement, item.status, item.evidence, item.observation] for item in report.conformity]
    return [
        paragraph("Rezumat de conformare checklist", style="Heading1"),
        table(["Cerință", "DA/NU", "Dovezi în raport", "Observații"], rows),
    ]


def build_exercise_section(report: AuditChecklistReport) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    return [
        paragraph("01_EXERCITIU — Fișa principală a exercițiului", style="Heading1"),
        table(
            ["Element", "Valoare"],
            [
                ["Cod produs", exercise.code],
                ["Lot produs", exercise.lot],
                ["Denumire produs", exercise.product_name],
                ["Tip caz", exercise.case_type],
                ["Data generării", date.today().isoformat()],
                ["Rezultat", exercise.result],
                ["Surse", ", ".join(exercise.generated_from_sources) or "FARA DATE IDENTIFICATE"],
            ],
        ),
        paragraph("Bilanț produs finit", style="Heading2"),
        table(
            ["Element", "Valoare", "Observație"],
            [
                ["Total produs PRD", balance.prd_produced, "Sursă suport: PRD PRE_*"],
                ["WMS PRODUCTION-OUT", balance.wms_production_out, "Sursă oficială: WMS"],
                ["Total livrat WMS", balance.wms_delivered, "Sursă oficială: WMS livrări"],
                ["Stoc la moment", balance.stock_at_moment, "Dacă lotul PF există în stoc"],
                ["Ajustări", balance.adjustments, "Corecții/ajustări WMS dacă sunt disponibile"],
                ["Status bilanț", balance.status, balance.observation],
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
            delivery.observation,
        ]
        for delivery in report.downstream
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 8]
    return [
        paragraph("03_TABEL_II_AVAL — Livrări produs finit", style="Heading1"),
        paragraph("Tabelul II este separat pe câmpurile cerute în checklist: client, adresă, dată livrare, cantitate și document livrare."),
        table(["Client", "Adresă", "Dată livrare", "Cantitate livrată", "Tip document", "Număr document", "Comandă WMS", "Observații"], rows),
    ]


def build_upstream_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [
            line.material_type,
            line.code,
            line.lot,
            line.name,
            line.consumed_quantity,
            line.receipt_date,
            line.supplier,
            line.document_type,
            line.document_number,
            line.document_date,
            line.stock_at_moment,
            line.third_party_delivery_status,
            line.observation,
        ]
        for line in report.upstream
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 13]
    return [
        paragraph("02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare", style="Heading1"),
        paragraph("Tabelul I este separat pe câmpurile cerute în checklist: lot, recepție, furnizor, document, dată document, stoc și observații."),
        table(["Tip", "Cod", "Lot", "Denumire", "Cantitate consumată", "Dată recepție", "Furnizor", "Tip document", "Număr document", "Dată document", "Stoc la moment", "Livrări terți", "Observații"], rows),
        *build_third_party_section(report),
    ]


def build_third_party_section(report: AuditChecklistReport) -> list[str]:
    raw_lines = [line for line in report.upstream if line.material_type == "Materie primă"]
    if not raw_lines:
        return []
    rows = [[line.code, line.lot, line.name, line.consumed_quantity, line.third_party_delivery_status, line.observation] for line in raw_lines]
    return [
        paragraph("Verificare specială: materii prime livrate către terți", style="Heading2"),
        table(["Cod MP", "Lot MP", "Denumire", "Consum în lot auditat", "Livrări MP către terți", "Observații"], rows),
    ]


def build_production_consumption_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [
            row.production_order,
            row.production_date,
            row.finished_product_quantity,
            row.wms_production_out,
            row.associated_delivery,
            row.material_type,
            row.consumed_code,
            row.consumed_lot,
            row.consumed_name,
            row.consumed_quantity,
        ]
        for row in report.production_consumption
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 10]
    return [
        paragraph("04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție", style="Heading1"),
        paragraph("Tabel operațional pentru verificarea separată a fiecărei comenzi de producție și a consumurilor aferente."),
        table(["Comandă producție", "Dată producție", "Cantitate PF PRD", "WMS PRODUCTION-OUT", "Livrare PF asociată", "Tip consum", "Cod consum", "Lot consum", "Denumire consum", "Cantitate consum"], rows),
    ]


def build_lot_flow_section(report: AuditChecklistReport) -> list[str]:
    rows = [
        [flow.material_type, flow.code, flow.lot, flow.name, flow.receipts, flow.consumed_in_audited_lot, flow.third_party_deliveries, flow.stock_at_moment, flow.status, flow.observation]
        for flow in report.lot_flows
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 10]
    return [
        paragraph("05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente", style="Heading1"),
        table(["Tip", "Cod", "Lot", "Denumire", "Recepții", "Consum lot auditat", "Livrări terți", "Stoc", "Status", "Observație"], rows),
    ]


def build_document_register_section(report: AuditChecklistReport) -> list[str]:
    rows = [[line.area, line.document_type, line.document_reference, line.related_code, line.related_lot, line.related_order, line.why_needed, line.status] for line in report.document_register]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 8]
    return [
        paragraph("Registru documente fizice de pregătit pentru auditor", style="Heading2"),
        table(["Zona", "Tip document", "Referință", "Cod", "Lot", "Comandă", "Motiv", "Status"], rows),
    ]


def build_conclusion_section(report: AuditChecklistReport) -> list[str]:
    parts = [
        paragraph("Concluzie audit intern", style="Heading1"),
        paragraph(f"Status: {report.conclusion_status}", bold=True),
        paragraph(report.conclusion_text),
    ]
    if report.observations:
        parts.append(paragraph("Observații", style="Heading2"))
        parts.extend(bullets(report.observations))
    return parts


def build_sources_section(report: AuditChecklistReport) -> list[str]:
    return [
        paragraph("Surse analizate", style="Heading1"),
        *bullets(report.exercise.generated_from_sources or ["FARA DATE IDENTIFICATE"]),
    ]


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
