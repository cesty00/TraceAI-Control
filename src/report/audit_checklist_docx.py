"""Checklist-aligned audit DOCX renderer.

This renderer consumes AuditChecklistReport, not raw TraceabilityCase tables. It
keeps the report audit-oriented: concise text, explicit sections and stable
WordprocessingML output.
"""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from src.audit.audit_checklist_report import (
    AuditChecklistReport,
    ChecklistDocumentRegisterLine,
    ChecklistLotFlow,
    ChecklistProductionConsumption,
    ChecklistUpstreamLine,
    build_audit_checklist_report,
)
from src.audit.audit_traceability_report import build_audit_traceability_report
from src.core.build_info import BuildInfo, build_info_table_rows, get_build_info
from src.report.audit_docx import (
    APP_XML,
    CONTENT_TYPES_XML,
    CORE_XML,
    DOCUMENT_RELS_XML,
    ROOT_RELS_XML,
    STYLES_XML,
    bullets,
    page_break,
    paragraph,
    wrap_document,
)
from src.report.docx_layout import (
    apply_cell_layout_properties,
    apply_table_layout_properties,
    compact_audit_table,
    table_row_properties_xml,
)
from src.rules.run_traceability_case import run_traceability_case

MISSING = "FARA DATE IDENTIFICATE"
DOCUMENT_REGISTER_CHECKBOX = "☐"
QUICK_AUDITOR_GUIDE_ITEMS = [
    "Verifică întâi Rezumatul de conformare checklist.",
    "Confirmă bilanțul PRD vs WMS în 01_EXERCITIU.",
    "Verifică avalul în 03_TABEL_II_AVAL și documentele de livrare.",
    "Verifică amontele în 02_TABEL_I_AMONTE și documentele de recepție.",
    "Folosește registrul documentelor pentru pregătirea dosarului fizic.",
]


@dataclass(frozen=True)
class AuditReportPolicy:
    """Controls how much detail is visible in the audit DOCX."""

    max_name_chars: int = 42
    max_observation_chars: int = 70
    max_receipt_chars: int = 120
    max_delivery_chars: int = 80
    max_register_reference_chars: int = 120
    max_visible_lot_flows: int = 12
    max_visible_document_register_rows: int = 18
    target_page_count: int = 6

    def short(self, value: object, max_length: int | None = None) -> str:
        limit = max_length or self.max_observation_chars
        text = str(value).strip() if value is not None else MISSING
        if not text:
            text = MISSING
        text = re.sub(r"\s+", " ", text)
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"

    def name(self, value: object) -> str:
        return self.short(value, self.max_name_chars)

    def delivery(self, value: object) -> str:
        return self.short(value, self.max_delivery_chars)

    def stock(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        return text.replace("locații:", "loc.")

    def receipts(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        parts = [part.strip() for part in text.split(";") if part.strip()]
        if len(parts) <= 2:
            return self.short(text, self.max_receipt_chars)
        return self.short(f"{parts[0]}; {parts[1]}; +{len(parts) - 2} alte", self.max_receipt_chars)

    def third_party(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        if text.startswith("DA;"):
            return self.short(text, 85)
        if "nu se aplic" in text.casefold():
            return "Nu se aplică"
        return self.short(text, 85)

    def upstream_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else "OK"
        if not text or text == "OK":
            return "OK"
        folded = text.casefold()
        if "nu se aplic" in folded:
            return "Nu se aplică"
        if "nu apare în stoc" in folded or "stoc" in folded:
            return "Stoc nedisponibil în fișier"
        if "livrări către terți" in folded:
            return "Verificat livrări terți"
        if "recep" in folded:
            return "Verificare recepții"
        return self.short(text, self.max_observation_chars)

    def downstream_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else "OK"
        if not text or text == MISSING:
            return "OK"
        return "Document WMS; data/adresa se completează dacă există în sursă"

    def third_party_note(self, line: ChecklistUpstreamLine) -> str:
        if line.third_party_delivery_status == "NU":
            return "Nu au fost identificate livrări directe în WMS."
        if line.third_party_delivery_status == "DA":
            return self.short(line.observation, 85)
        return self.short(line.observation, 85)

    def flow_status(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if "parțial" in text:
            return "documentat parțial"
        return self.short(text, 35)

    def flow_observation(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return "OK"
        folded = text.casefold()
        if "nu se aplic" in folded:
            return "Nu se aplică"
        if "stoc" in folded:
            return "Verificare stoc"
        if "livrări" in folded:
            return "Verificare livrări"
        return self.short(text, 60)

    def register_reference(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        if not text or text == MISSING:
            return MISSING
        return self.receipts(text)

    def register_reason(self, value: object) -> str:
        text = str(value).strip() if value is not None else MISSING
        folded = text.casefold()
        if "produc" in folded:
            return "Confirmă producția și consumurile"
        if "livrare" in folded:
            return "Confirmă livrarea aval"
        if "intrarea" in folded or "recep" in folded:
            return "Confirmă intrarea lotului sursă"
        return self.short(text, 55)

    def select_lot_flows(self, rows: Sequence[ChecklistLotFlow]) -> list[ChecklistLotFlow]:
        important: list[ChecklistLotFlow] = []
        secondary: list[ChecklistLotFlow] = []
        for row in rows:
            text = f"{row.material_type} {row.third_party_deliveries} {row.stock_at_moment} {row.observation}".casefold()
            if row.material_type in {"Materie primă", "Material auxiliar / gaz"} or "da" in text or "fara date" not in text:
                important.append(row)
            else:
                secondary.append(row)
        return (important + secondary)[: self.max_visible_lot_flows]

    def select_document_register(self, rows: Sequence[ChecklistDocumentRegisterLine]) -> list[ChecklistDocumentRegisterLine]:
        priority = {"PRD": 0, "WMS": 1, "NIR": 2}
        return sorted(rows, key=lambda row: (priority.get(row.area, 9), row.related_code, row.related_lot, row.document_reference))[: self.max_visible_document_register_rows]

    def overflow_note(self, total: int, visible: int, label: str) -> str | None:
        if total <= visible:
            return None
        return f"+{total - visible} {label} suplimentare sunt păstrate în datele tehnice ale cazului."


DEFAULT_POLICY = AuditReportPolicy()


def table(headers: list[str], rows: list[list[object]]) -> str:
    """Render major audit checklist tables using the compact visual design renderer."""

    return compact_audit_table(headers, rows)


def build_checklist_header_xml(report: AuditChecklistReport, build_info: BuildInfo) -> str:
    """Build the audit checklist DOCX header with case metadata.

    The checklist report is intended to be printed and reviewed page by page, so
    every page needs enough context to identify the audit case without changing
    the document body or any extraction logic.
    """

    code = _header_footer_text(report.exercise.code)
    lot = _header_footer_text(report.exercise.lot)
    product_name = _header_footer_text(report.exercise.product_name)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:spacing w:after="0"/></w:pPr>
    <w:r><w:rPr><w:b/><w:sz w:val="15"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t>TraceAI Control — Test de trasabilitate pentru audit</w:t></w:r>
    <w:r><w:rPr><w:sz w:val="15"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t> | Cod {code} | Lot {lot}</w:t></w:r>
  </w:p>
  <w:p>
    <w:pPr><w:spacing w:after="0"/></w:pPr>
    <w:r><w:rPr><w:sz w:val="13"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t>{product_name}</w:t></w:r>
  </w:p>
</w:hdr>
'''


def build_checklist_footer_xml(report: AuditChecklistReport, build_info: BuildInfo) -> str:
    """Build the audit checklist DOCX footer with build and page metadata."""

    version = _header_footer_text(build_info.app_version)
    commit = _header_footer_text(build_info.short_commit)
    channel = _header_footer_text(build_info.build_channel)
    generated_at = _header_footer_text(build_info.generated_at)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:spacing w:after="0"/><w:jc w:val="center"/></w:pPr>
    <w:r><w:rPr><w:sz w:val="13"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t>TraceAI Control {version} | commit {commit} | canal {channel} | generat {generated_at} | pagina </w:t></w:r>
    <w:fldSimple w:instr="PAGE"><w:r><w:rPr><w:sz w:val="13"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>
  </w:p>
</w:ftr>
'''


def _header_footer_text(value: object) -> str:
    text = str(value).strip() if value is not None else MISSING
    return html.escape(text or MISSING, quote=False)


def generate_audit_checklist_docx_report(
    report: AuditChecklistReport,
    output_path: str | Path,
    policy: AuditReportPolicy = DEFAULT_POLICY,
    build_info: BuildInfo | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata = build_info or get_build_info()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        package.writestr("_rels/.rels", ROOT_RELS_XML)
        package.writestr("docProps/app.xml", APP_XML)
        package.writestr("docProps/core.xml", CORE_XML)
        package.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        package.writestr("word/styles.xml", STYLES_XML)
        package.writestr("word/header1.xml", build_checklist_header_xml(report, metadata))
        package.writestr("word/footer1.xml", build_checklist_footer_xml(report, metadata))
        package.writestr("word/document.xml", build_document_xml(report, policy, metadata))
    return output


def build_document_xml(
    report: AuditChecklistReport,
    policy: AuditReportPolicy = DEFAULT_POLICY,
    build_info: BuildInfo | None = None,
) -> str:
    metadata = build_info or get_build_info()
    body: list[str] = []
    body.extend(build_title_block(report, metadata))
    body.extend(build_auditor_verdict_card_section(report, policy))
    body.extend(build_quick_auditor_guide_section())
    body.extend(build_conformity_section(report, policy))
    body.extend(build_exercise_section(report, policy))
    body.extend(build_downstream_section(report, policy))
    body.append(page_break())
    body.extend(build_upstream_section(report, policy))
    body.append(page_break())
    body.extend(build_production_consumption_section(report, policy))
    body.append(page_break())
    body.extend(build_lot_flow_section(report, policy))
    body.extend(build_document_register_section(report, policy))
    body.extend(build_conclusion_section(report, policy))
    body.extend(build_build_info_section(metadata))
    return wrap_document("".join(body))


def build_title_block(report: AuditChecklistReport, build_info: BuildInfo) -> list[str]:
    return [
        paragraph("TEST DE TRASABILITATE PENTRU AUDIT", style="Title"),
        paragraph(f"{report.exercise.code} / {report.exercise.lot} — {report.exercise.product_name}", bold=True, align="center"),
        paragraph("Raport completat din fișierele sursă disponibile: WMS trasabilitate, raport producție, stoc la moment și nomenclator.", align="center"),
        literal_paragraph(f"Build raport: {build_info.app_version} / commit {build_info.short_commit} / generat {build_info.generated_at}", align="center"),
    ]


def build_auditor_verdict_card_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    return [
        paragraph("Card verdict auditor", style="Heading1"),
        paragraph("Rezumat executiv pentru prima pagină: identifică rapid produsul, lotul, verdictul și zonele care trebuie verificate în dosarul de audit."),
        table(
            ["Indicator audit", "Status / valoare"],
            [
                ["Verdict audit", report.conclusion_status],
                ["Cod produs", report.exercise.code],
                ["Lot", report.exercise.lot],
                ["Denumire produs", policy.name(report.exercise.product_name)],
                ["Bilanț PRD vs WMS", f"{report.balance.status} — {policy.short(report.balance.observation, 90)}"],
                ["Aval / livrări", f"{len(report.downstream)} livrări identificate" if report.downstream else MISSING],
                ["Amonte / loturi sursă", f"{len(report.upstream)} linii amonte identificate" if report.upstream else MISSING],
                ["Documente fizice", f"{len(report.document_register)} documente de pregătit" if report.document_register else MISSING],
            ],
        ),
    ]


def build_quick_auditor_guide_section() -> list[str]:
    return [
        paragraph("Ghid rapid pentru auditor", style="Heading1"),
        paragraph("Acest ghid indică ordinea recomandată de citire a raportului și documentele care trebuie verificate prioritar."),
        *bullets(QUICK_AUDITOR_GUIDE_ITEMS),
    ]


def build_conformity_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[item.requirement, item.status, policy.short(item.evidence, 95), policy.short(item.observation, 95)] for item in report.conformity]
    return [
        paragraph("Rezumat de conformare checklist", style="Heading1"),
        paragraph("Acest rezumat arată, într-o formă scurtă, dacă principalele cerințe ale exercițiului de trasabilitate sunt acoperite de datele identificate. Statusul DA indică faptul că raportul conține informațiile necesare pentru verificare; observațiile explică eventualele limite sau completări necesare."),
        table(["Cerință", "Status în test", "Dovezi", "Observații"], rows),
    ]


def build_exercise_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    return [
        paragraph("01_EXERCITIU — Fișa principală a exercițiului", style="Heading1"),
        paragraph("Fișa principală fixează produsul și lotul analizat. Această secțiune este punctul de plecare al verificării și trebuie citită împreună cu Tabelul I pentru amonte și Tabelul II pentru aval."),
        table(["Indicator", "Valoare"], [["Cod produs", exercise.code], ["Lot produs", exercise.lot], ["Denumire produs", exercise.product_name], ["Status verificare", exercise.result]]),
        paragraph("Bilanț produs finit", style="Heading2"),
        paragraph("Bilanțul compară cantitatea produsă în PRD cu intrările și ieșirile lotului în WMS. Scopul este să confirme că lotul produs poate fi urmărit până la livrările către clienți sau până la stocul rămas."),
        table(["Indicator", "Cantitate / status", "Observație"], [["Total produs PRD", balance.prd_produced, "Sursă PRD"], ["WMS PRODUCTION-OUT", balance.wms_production_out, "Intrare produs finit WMS"], ["Total livrat WMS", balance.wms_delivered, "Valoare semnată WMS"], ["Stoc la moment", balance.stock_at_moment, "Dacă există în stoc"], ["Status bilanț", balance.status, policy.short(balance.observation, 90)]]),
    ]


def build_downstream_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[d.client, d.address, d.delivery_date, d.delivered_quantity, d.delivery_document_type, d.delivery_document_number, d.wms_order, policy.downstream_observation(d.observation)] for d in report.downstream]
    if not rows:
        rows = [[MISSING] * 8]
    return [paragraph("03_TABEL_II_AVAL — Livrări produs finit", style="Heading1"), paragraph("Tabelul II prezintă traseul lotului de produs finit către clienți. Pentru fiecare livrare sunt afișate clientul, adresa sau depozitul identificat, data livrării, cantitatea livrată și documentul WMS care susține ieșirea din gestiune."), table(["Client", "Adresă", "Dată livrare", "Cantitate livrată", "Tip document", "Număr document", "Comandă WMS", "Observații"], rows)]


def build_upstream_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    rows = [[line.material_type, line.code, line.lot, policy.name(line.name), line.consumed_quantity, line.receipt_date, policy.name(line.supplier), line.document_type, line.document_number, line.document_date, policy.stock(line.stock_at_moment), line.third_party_delivery_status, policy.upstream_observation(line.observation)] for line in report.upstream]
    if not rows:
        rows = [[MISSING] * 13]
    return [paragraph("02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare", style="Heading1"), paragraph("Tabelul I urmărește loturile care au intrat în produsul finit: materii prime, ambalaje și materiale auxiliare, inclusiv gazul atunci când este folosit. Pentru fiecare lot sunt afișate consumul, furnizorul, documentul de recepție, stocul disponibil și observațiile relevante pentru audit."), table(["Tip", "Cod", "Lot", "Denumire", "Consum", "Dată recepție", "Furnizor", "Tip document", "Număr document", "Dată document", "Stoc la moment", "Livrări terți", "Observații"], rows), *build_third_party_section(report, policy)]


def build_third_party_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    raw_lines = [line for line in report.upstream if line.material_type == "Materie primă"]
    if not raw_lines:
        return []
    rows = [[line.code, line.lot, policy.name(line.name), line.consumed_quantity, line.third_party_delivery_status, policy.third_party_note(line)] for line in raw_lines]
    return [paragraph("Verificare specială — materii prime livrate către terți", style="Heading2"), paragraph("Această verificare evidențiază dacă loturile de materie primă folosite în produsul auditat au avut și livrări directe către terți. Informația este importantă pentru separarea consumului intern de alte ieșiri ale aceluiași lot sursă."), table(["Cod MP", "Lot MP", "Denumire", "Consum în lot", "Livrări MP către terți", "Detalii"], rows)]


def build_production_consumption_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    return [paragraph("04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție", style="Heading1"), paragraph("Această secțiune leagă comenzile de producție de cantitatea de produs finit obținută și de materialele consumate. Ea ajută auditorul să verifice, pe fiecare comandă, din ce loturi s-a produs lotul finit analizat."), paragraph("Comenzi producție", style="Heading2"), paragraph("Tabelul de comenzi sintetizează producția pe fiecare comandă și asocierea cu intrarea WMS PRODUCTION-OUT și cu livrarea produsului finit, atunci când aceasta poate fi legată de cantitate și document."), table(["Comandă producție", "Dată producție", "Cantitate PRD", "WMS production-out", "Livrare PF asociată"], production_order_summary_rows(report.production_consumption, policy)), paragraph("Consumuri pe comenzi — tabel operațional", style="Heading2"), paragraph("Tabelul operațional detaliază consumurile aferente fiecărei comenzi: materii prime, ambalaje și materiale auxiliare. Cantitățile sunt cele preluate din PRD și sunt folosite pentru a demonstra legătura dintre loturile sursă și produsul finit."), table(["Comandă", "Tip", "Cod consum", "Lot consum", "Denumire consum", "Cantitate consum"], production_consumption_rows(report.production_consumption, policy))]


def production_order_summary_rows(rows: list[ChecklistProductionConsumption], policy: AuditReportPolicy) -> list[list[str]]:
    summary: OrderedDict[str, ChecklistProductionConsumption] = OrderedDict()
    for row in rows:
        summary.setdefault(row.production_order, row)
    if not summary:
        return [[MISSING] * 5]
    return [[row.production_order, row.production_date, row.finished_product_quantity, row.wms_production_out, policy.delivery(row.associated_delivery)] for row in summary.values()]


def production_consumption_rows(rows: list[ChecklistProductionConsumption], policy: AuditReportPolicy) -> list[list[str]]:
    if not rows:
        return [[MISSING] * 6]
    return [[row.production_order, row.material_type, row.consumed_code, row.consumed_lot, policy.name(row.consumed_name), row.consumed_quantity] for row in rows]


def build_lot_flow_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    selected = policy.select_lot_flows(report.lot_flows)
    rows = [[flow.material_type, flow.code, flow.lot, policy.name(flow.name), policy.receipts(flow.receipts), flow.consumed_in_audited_lot, policy.third_party(flow.third_party_deliveries), policy.stock(flow.stock_at_moment), policy.flow_status(flow.status), policy.flow_observation(flow.observation)] for flow in selected]
    if not rows:
        rows = [[MISSING] * 10]
    parts = [paragraph("05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente", style="Heading1"), paragraph("Fluxurile de loturi reunesc informațiile esențiale despre recepții, consumul în lotul auditat, eventualele livrări către terți și stocul rămas. Tabelul este o privire de ansamblu asupra mișcărilor relevante pentru fiecare lot sursă."), table(["Tip", "Cod", "Lot", "Denumire", "Recepții", "Consum auditat", "Livrări terți", "Stoc", "Status", "Observații"], rows)]
    note = policy.overflow_note(len(report.lot_flows), len(selected), "fluxuri")
    if note:
        parts.append(paragraph(note))
    return parts


def build_document_register_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    selected = policy.select_document_register(report.document_register)
    rows = [[DOCUMENT_REGISTER_CHECKBOX, line.area, line.document_type, policy.register_reference(line.document_reference), line.related_code, line.related_lot, policy.delivery(line.related_order), policy.register_reason(line.why_needed), line.status] for line in selected]
    if not rows:
        rows = [[MISSING] * 9]
    parts = [paragraph("Registru documente fizice de pregătit pentru auditor", style="Heading2"), paragraph("Registrul indică documentele care trebuie pregătite în dosarul de audit. Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită pentru documentele fizice."), table(["Bifat", "Zona", "Tip document", "Referință", "Cod", "Lot", "Comandă", "Motiv", "Status"], rows)]
    note = policy.overflow_note(len(report.document_register), len(selected), "documente")
    if note:
        parts.append(paragraph(note))
    return parts


def build_conclusion_section(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    return [
        paragraph("Concluzie audit intern", style="Heading1"),
        paragraph(f"Pentru produsul {report.exercise.code} / lot {report.exercise.lot}, raportul audit confirmă trasabilitatea produsului finit în aval și în amonte pe baza surselor WMS și PRD disponibile."),
        paragraph("Concluzia sintetizează rezultatul verificării pe baza datelor WMS și PRD disponibile. Ea nu înlocuiește verificarea documentelor fizice, ci indică ce a fost identificat și ce trebuie atașat dosarului de audit."),
        paragraph(f"Bilanț PRD vs WMS: {report.balance.status}. {policy.short(report.balance.observation, 120)}"),
        *bullets(compact_conclusion_observations(report, policy)),
    ]


def compact_conclusion_observations(report: AuditChecklistReport, policy: AuditReportPolicy) -> list[str]:
    raw_materials = [line for line in report.upstream if line.material_type == "Materie primă"]
    packaging = [line for line in report.upstream if line.material_type == "Ambalaj"]
    gases = [line for line in report.upstream if "gaz" in line.material_type.casefold()]
    return [f"S-au identificat {len(raw_materials)} materii prime, {len(packaging)} ambalaje și {len(gases)} linii auxiliare/gaz în amonte.", "Recepțiile WMS disponibile și stocurile la moment sunt afișate în Tabelul I și în fluxurile de loturi.", "Raportul poate fi folosit ca bază pentru pregătirea dosarului de audit, împreună cu documentele fizice menționate în registru."]


def build_build_info_section(build_info: BuildInfo) -> list[str]:
    return [paragraph("Informații build raport", style="Heading1"), paragraph("Această secțiune identifică versiunea aplicației folosită la generarea raportului, pentru corelare cu diagnosticele GitHub și build-urile instalate local."), literal_table(["Câmp", "Valoare"], build_info_table_rows(build_info))]


def literal_paragraph(text: object, style: str | None = None, bold: bool = False, align: str | None = None) -> str:
    style_xml = f'<w:pStyle w:val="{style}"/>' if style else ""
    align_xml = f'<w:jc w:val="{align}"/>' if align else ""
    bold_xml = "<w:b/>" if bold else ""
    return f"<w:p><w:pPr>{style_xml}{align_xml}</w:pPr><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{html.escape(str(text), quote=False)}</w:t></w:r></w:p>"


def literal_table(headers: list[str], rows: list[list[object]]) -> str:
    xml_rows = [literal_table_row(headers, is_header=True)]
    xml_rows.extend(literal_table_row(row) for row in rows)
    borders = "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/></w:tblBorders>"
    table_properties = apply_table_layout_properties('<w:tblStyle w:val="TraceAITable"/>')
    return f"<w:tbl><w:tblPr>{table_properties}{borders}</w:tblPr>{''.join(xml_rows)}</w:tbl>"


def literal_table_row(values: Iterable[object], is_header: bool = False) -> str:
    return f"<w:tr>{table_row_properties_xml(is_header)}{''.join(literal_table_cell(value, is_header=is_header) for value in values)}</w:tr>"


def literal_table_cell(value: object, is_header: bool = False) -> str:
    shading_xml = '<w:shd w:fill="EDEDED"/>' if is_header else ""
    bold_xml = "<w:b/>" if is_header else ""
    size = "15" if is_header else "14"
    text = str(value).strip() if value is not None else MISSING
    cell_properties = apply_cell_layout_properties(
        f'{shading_xml}<w:tcMar><w:top w:w="40" w:type="dxa"/><w:left w:w="40" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="40" w:type="dxa"/></w:tcMar>'
    )
    return f"<w:tc><w:tcPr>{cell_properties}</w:tcPr><w:p><w:pPr><w:spacing w:after=\"0\"/></w:pPr><w:r><w:rPr>{bold_xml}<w:sz w:val=\"{size}\"/><w:rFonts w:ascii=\"Arial\" w:hAnsi=\"Arial\"/></w:rPr><w:t>{html.escape(text or MISSING, quote=False)}</w:t></w:r></w:p></w:tc>"


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
