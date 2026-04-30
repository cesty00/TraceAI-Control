"""Audit DOCX renderer for TraceAI Control.

The renderer follows the scanned audit model:
- TEST DE TRASABILITATE PENTRU AUDIT title
- 01_EXERCITIU on the first page, with finished-product balance
- 03_TABEL_II_AVAL downstream deliveries after the balance
- 02_TABEL_I_AMONTE upstream materials
- one block per production order
- 05_FLUX_LOTURI_SI_DOCUMENTE, document register, conclusion and sources
"""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from src.audit.audit_traceability_report import (
    AuditTraceabilityReport,
    PhysicalDocumentRequirement,
    ProductionOrderTrace,
    UpstreamMaterialLine,
    build_audit_traceability_report,
)
from src.rules.run_traceability_case import run_traceability_case

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

DOCUMENT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>
"""

APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>TraceAI Control</Application>
</Properties>
"""

CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>TEST DE TRASABILITATE PENTRU AUDIT</dc:title>
  <dc:creator>TraceAI Control</dc:creator>
</cp:coreProperties>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="80"/></w:pPr><w:rPr><w:sz w:val="17"/><w:szCs w:val="17"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:after="140"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="140" w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="20"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="100" w:after="60"/></w:pPr><w:rPr><w:b/><w:sz w:val="18"/><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TraceAITable"><w:name w:val="TraceAI Audit Table"/></w:style>
</w:styles>
"""

HEADER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:rPr><w:b/><w:sz w:val="16"/></w:rPr><w:t>TraceAI Control — Test de trasabilitate general pentru audit intern</w:t></w:r></w:p></w:hdr>
"""

FOOTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:rPr><w:sz w:val="14"/></w:rPr><w:t>TraceAI Control — Test de trasabilitate general pentru audit intern</w:t></w:r></w:p></w:ftr>
"""


def generate_audit_docx_report(report: AuditTraceabilityReport, output_path: str | Path) -> Path:
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


def build_document_xml(report: AuditTraceabilityReport) -> str:
    body: list[str] = []
    body.extend(build_title_block(report))
    body.extend(build_exercise_section(report))
    body.extend(build_downstream_section(report))
    body.append(page_break())
    body.extend(build_upstream_section(report))
    body.append(page_break())
    body.extend(build_production_section(report))
    body.append(page_break())
    body.extend(build_lot_flow_and_documents_section(report))
    body.extend(build_conclusion_section(report))
    body.extend(build_sources_section(report))
    return wrap_document("".join(body))


def build_title_block(report: AuditTraceabilityReport) -> list[str]:
    exercise = report.exercise
    return [
        paragraph("TEST DE TRASABILITATE PENTRU AUDIT", style="Title"),
        paragraph(f"{exercise.code} / {exercise.lot} — {exercise.product_name}", bold=True, align="center"),
        paragraph(
            "Document generat pe baza manualului de verificare a trasabilității: surse WMS, raport producție, nomenclator și stoc la moment.",
            align="center",
        ),
    ]


def build_exercise_section(report: AuditTraceabilityReport) -> list[str]:
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
                ["Rezultat reconciliere", exercise.traceability_result],
                ["Observație", balance.balance_observation],
            ],
        ),
        paragraph("Bilanț produs finit", style="Heading2"),
        paragraph("Regulă aplicată: WMS este sursa oficială pentru mișcări și livrări; PRD este sursa suport pentru comenzi, consumuri, ambalaje și materiale auxiliare."),
        table(
            ["Element", "Cantitate / formulă", "Observație"],
            [
                ["Total produs PRD", join_quantity(balance.prd_produced_quantity, balance.prd_produced_um), "Produse finite declarate în PRD"],
                ["WMS PRODUCTION-OUT", join_quantity(balance.wms_production_out_quantity, balance.wms_production_out_um), "Confirmă intrarea PF în stoc la moment"],
                ["Total livrat WMS", join_quantity(balance.wms_delivered_quantity, balance.wms_delivered_um), "Livrările sunt valori semnate WMS"],
                ["Stoc la moment", join_quantity(balance.stock_quantity, balance.stock_um), "Dacă lotul există în stoc la moment"],
                ["Rezultat reconciliere PF", balance.balance_status, balance.balance_observation],
            ],
        ),
    ]


def build_downstream_section(report: AuditTraceabilityReport) -> list[str]:
    rows = [[d.delivery_date, d.order_number, d.document_number, d.client, join_quantity(d.quantity, d.um), d.rows] for d in report.downstream]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 6]
    return [
        paragraph("03_TABEL_II_AVAL — Livrări produs finit", style="Heading1"),
        paragraph("Comenzile și documentele de livrare sunt preluate din WMS. Pentru audit se atașează documentele fizice aferente fiecărei livrări."),
        table(["Data", "Comandă WMS", "Document comandă", "Client adresă WMS", "Cantitate", "Rânduri"], rows),
    ]


def build_upstream_section(report: AuditTraceabilityReport) -> list[str]:
    rows = [
        [
            display_category(line.category),
            line.code,
            line.lot,
            line.name,
            join_quantity(line.quantity_consumed, line.um),
            line.document_summary,
            display_third_party_status(line.third_party_delivery_status),
            line.stock_at_moment,
            observations_text(line),
        ]
        for line in report.upstream
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 9]
    return [
        paragraph("02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare", style="Heading1"),
        paragraph("Tabelul include intrările folosite în lotul auditat și documentele WMS disponibile. Pentru materiile prime se verifică explicit dacă există livrări directe către terți."),
        table(["Tip", "Cod", "Lot", "Denumire", "Cantitate consumată", "Documente WMS", "Livrări către terți", "Stoc la moment", "Observații"], rows),
        *build_raw_material_third_party_check(report),
    ]


def build_raw_material_third_party_check(report: AuditTraceabilityReport) -> list[str]:
    raw_lines = [line for line in report.upstream if line.category == "raw_material"]
    rows = [[line.code, line.lot, line.name, join_quantity(line.quantity_consumed, line.um), display_third_party_status(line.third_party_delivery_status), line.third_party_delivery_details, line.stock_at_moment] for line in raw_lines]
    if not rows:
        return []
    return [
        paragraph("Verificare specială: livrări către terți pentru materii prime", style="Heading2"),
        table(["Cod MP", "Lot MP", "Denumire", "Consum în lot auditat", "Livrări MP către terți", "Detalii", "Stoc la moment"], rows),
    ]


def build_production_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [paragraph("04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție", style="Heading1")]
    if not report.production_orders:
        return parts + [paragraph("FARA DATE IDENTIFICATE")]
    for index, order in enumerate(report.production_orders):
        if index > 0:
            parts.append(page_break())
        parts.extend(build_production_order_block(order))
    return parts


def build_production_order_block(order: ProductionOrderTrace) -> list[str]:
    parts = [
        paragraph(f"Comanda producție {order.production_order}", style="Heading1"),
        table(
            ["Element", "Valoare"],
            [
                ["Cod/Lot PRD", f"{order.finished_product_code} / {order.finished_product_lot}"],
                ["Produs finit", order.finished_product_name],
                ["Cantitate PRD", join_quantity(order.prd_quantity, order.prd_um)],
                ["WMS PRODUCTION-OUT comandă", join_quantity(order.wms_production_out_quantity, order.wms_production_out_um)],
                ["Livrare PF asociată", order.associated_delivery],
                ["Data schimb/linie", "FARA DATE IDENTIFICATE"],
            ],
        ),
    ]
    parts.extend(material_lines_table("Materii prime", order.raw_materials, include_third_party=True))
    parts.extend(material_lines_table("Ambalaje", order.packaging, include_third_party=False))
    parts.extend(material_lines_table("Materiale auxiliare / gaz", order.auxiliaries_gas, include_third_party=False))
    if order.observations:
        parts.append(paragraph("Observații comandă", style="Heading2"))
        parts.extend(bullets(order.observations))
    return parts


def material_lines_table(title: str, lines: list[UpstreamMaterialLine], include_third_party: bool) -> list[str]:
    if not lines:
        return [paragraph(title, style="Heading2"), paragraph("FARA DATE IDENTIFICATE")]
    headers = ["Cod", "Lot", "Denumire", "Cantitate consumată", "Livrări către terți"] if include_third_party else ["Cod", "Lot", "Denumire", "Cantitate consumată", "Observații"]
    rows: list[list[str]] = []
    for line in lines:
        if include_third_party:
            rows.append([line.code, line.lot, line.name, join_quantity(line.quantity_consumed, line.um), display_third_party_status(line.third_party_delivery_status)])
        else:
            rows.append([line.code, line.lot, line.name, join_quantity(line.quantity_consumed, line.um), observations_text(line) or "Nu se aplică"])
    return [paragraph(title, style="Heading2"), table(headers, rows)]


def build_lot_flow_and_documents_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [paragraph("05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente fizice", style="Heading1")]
    flow_rows = [
        [flow.category, flow.code, flow.lot, flow.name, flow.receipt_total, flow.consumed_in_audited_lot, flow.third_party_delivered_total, flow.stock_at_moment, flow.observation]
        for flow in report.source_lot_flows
    ]
    if not flow_rows:
        flow_rows = [["FARA DATE IDENTIFICATE"] * 9]
    parts.append(paragraph("Fluxuri loturi", style="Heading2"))
    parts.append(table(["Categorie", "Cod", "Lot", "Denumire", "Recepții", "Consum lot auditat", "Livrări terți", "Stoc", "Observație"], flow_rows))
    parts.append(paragraph("Registru documente fizice de pregătit pentru auditor", style="Heading2"))
    parts.append(table(["Zona", "Tip document", "Document / referință", "Cod", "Lot", "Comandă", "Motiv", "Status"], document_rows(report.physical_documents)))
    return parts


def document_rows(documents: list[PhysicalDocumentRequirement]) -> list[list[str]]:
    if not documents:
        return [["FARA DATE IDENTIFICATE"] * 8]
    return [[doc.document_area, doc.document_type, doc.document_reference, doc.related_code, doc.related_lot, doc.related_order, doc.why_needed, doc.status] for doc in documents]


def build_conclusion_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [
        paragraph("Concluzie audit intern", style="Heading1"),
        paragraph(f"Pentru produsul {report.exercise.code} / lot {report.exercise.lot}, testul de trasabilitate a fost generat pe baza datelor WMS și PRD disponibile."),
        paragraph(f"Status: {report.conclusion.status}"),
        paragraph(report.conclusion.summary),
    ]
    if report.conclusion.observations:
        parts.append(paragraph("Observații", style="Heading2"))
        parts.extend(bullets(report.conclusion.observations))
    return parts


def build_sources_section(report: AuditTraceabilityReport) -> list[str]:
    return [
        paragraph("Surse analizate", style="Heading1"),
        *bullets(report.exercise.data_sources or ["FARA DATE IDENTIFICATE"]),
        paragraph("Manual: structura 01_EXERCITIU, 02_TABEL_I_AMONTE, 03_TABEL_II_AVAL, 04_PRODUCTIE_CONSUM, 05_FLUX_LOTURI_SI_DOCUMENTE."),
    ]


def table(headers: list[str], rows: list[list[object]]) -> str:
    xml_rows = [table_row(headers, is_header=True)]
    xml_rows.extend(table_row(row) for row in rows)
    borders = "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/><w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"808080\"/></w:tblBorders>"
    return f"<w:tbl><w:tblPr><w:tblStyle w:val=\"TraceAITable\"/><w:tblW w:w=\"0\" w:type=\"auto\"/><w:tblLayout w:type=\"autofit\"/>{borders}</w:tblPr>{''.join(xml_rows)}</w:tbl>"


def table_row(values: Iterable[object], is_header: bool = False) -> str:
    return f"<w:tr>{''.join(table_cell(value, is_header=is_header) for value in values)}</w:tr>"


def table_cell(value: object, is_header: bool = False) -> str:
    shading_xml = '<w:shd w:fill="EDEDED"/>' if is_header else ""
    bold_xml = "<w:b/>" if is_header else ""
    size = "15" if is_header else "14"
    return f"<w:tc><w:tcPr>{shading_xml}<w:tcMar><w:top w:w=\"40\" w:type=\"dxa\"/><w:left w:w=\"40\" w:type=\"dxa\"/><w:bottom w:w=\"40\" w:type=\"dxa\"/><w:right w:w=\"40\" w:type=\"dxa\"/></w:tcMar></w:tcPr><w:p><w:pPr><w:spacing w:after=\"0\"/></w:pPr><w:r><w:rPr>{bold_xml}<w:sz w:val=\"{size}\"/><w:rFonts w:ascii=\"Arial\" w:hAnsi=\"Arial\"/></w:rPr><w:t>{escape(value_or_missing(value))}</w:t></w:r></w:p></w:tc>"


def paragraph(text: object, style: str | None = None, bold: bool = False, align: str | None = None) -> str:
    style_xml = f'<w:pStyle w:val="{style}"/>' if style else ""
    align_xml = f'<w:jc w:val="{align}"/>' if align else ""
    bold_xml = "<w:b/>" if bold else ""
    return f"<w:p><w:pPr>{style_xml}{align_xml}</w:pPr><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{escape(value_or_missing(text))}</w:t></w:r></w:p>"


def bullets(items: Iterable[object]) -> list[str]:
    return [paragraph(f"• {value_or_missing(item)}") for item in items]


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def join_quantity(quantity: object, unit: object) -> str:
    quantity_text = value_or_missing(quantity)
    unit_text = value_or_missing(unit)
    if quantity_text == "FARA DATE IDENTIFICATE" and unit_text == "FARA DATE IDENTIFICATE":
        return "FARA DATE IDENTIFICATE"
    if unit_text == "FARA DATE IDENTIFICATE":
        return quantity_text
    return f"{quantity_text} {unit_text}"


def display_category(category: str) -> str:
    labels = {"raw_material": "Materie primă", "packaging": "Ambalaj", "auxiliary_gas": "Material auxiliar / gaz"}
    return labels.get(category, category)


def display_third_party_status(status: object) -> str:
    labels = {"NU_SE_APLICA": "Nu se aplică", "NU": "NU", "DA": "DA", "NECLAR": "NECLAR"}
    return labels.get(str(status).strip(), value_or_missing(status))


def observations_text(line: UpstreamMaterialLine) -> str:
    return "; ".join(line.observations) if line.observations else ""


def value_or_missing(value: object) -> str:
    if value is None:
        return "FARA DATE IDENTIFICATE"
    text = str(value).strip()
    if not text:
        return "FARA DATE IDENTIFICATE"
    return format_audit_text(text)


def format_audit_text(text: str) -> str:
    """Format numeric fragments for human-readable audit output.

    The DTO can contain precise Decimal/float-derived strings from WMS and stock.
    The exported DOCX must be readable by an auditor, so values such as
    18236.000000000004 or 176.84306000002636 are rendered compactly while the
    internal calculation layer remains unchanged.
    """

    return re.sub(r"(?<![A-Za-z0-9])[-+]?\d+(?:[.,]\d+)?(?![A-Za-z0-9])", _format_numeric_match, text)


def _format_numeric_match(match: re.Match[str]) -> str:
    raw = match.group(0)
    if not should_format_number(raw):
        return raw
    try:
        value = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return raw
    return format_audit_decimal(value)


def should_format_number(raw: str) -> bool:
    if "." not in raw and "," not in raw:
        return False
    # Preserve lot/date-like tokens such as 27.03.26 when the regex sees only a part.
    if raw.count(".") > 1 or raw.count(",") > 1:
        return False
    return True


def format_audit_decimal(value: Decimal) -> str:
    if value == value.to_integral():
        return str(value.quantize(Decimal("1")))
    quantized = value.quantize(Decimal("0.001"))
    text = format(quantized.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def escape(value: str) -> str:
    return html.escape(value, quote=False)


def wrap_document(body_xml: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_xml}
    <w:sectPr>
      <w:headerReference w:type="default" r:id="rIdHeader1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
      <w:footerReference w:type="default" r:id="rIdFooter1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
      <w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>
      <w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="360" w:footer="360" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genereaza raport audit DOCX din AuditTraceabilityReport.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", required=True, help="Cale output DOCX.")
    args = parser.parse_args(argv)
    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    report = build_audit_traceability_report(traceability_case)
    generate_audit_docx_report(report, args.output)
    return 0 if report.exercise.traceability_result != "INCOMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
