"""Audit DOCX renderer for TraceAI Control.

This renderer consumes AuditTraceabilityReport, the audit-level DTO validated
against the manual report model. It is intentionally separate from
`docx_minimal.py`, which remains a diagnostic/fallback renderer.
"""

from __future__ import annotations

import argparse
import html
import zipfile
from datetime import date
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
  <dc:title>Raport audit trasabilitate TraceAI Control</dc:title>
  <dc:creator>TraceAI Control</dc:creator>
</cp:coreProperties>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="34"/><w:color w:val="1F4E79"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1F4E79"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="2F75B5"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TraceAITable"><w:name w:val="TraceAI Table"/></w:style>
</w:styles>
"""

HEADER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:rPr><w:b/><w:color w:val="1F4E79"/></w:rPr><w:t>TraceAI Control — Raport audit trasabilitate</w:t></w:r></w:p></w:hdr>
"""

FOOTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Raport audit generat din AuditTraceabilityReport. Uz intern / audit.</w:t></w:r></w:p></w:ftr>
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
    body.append(paragraph("RAPORT AUDIT TRASABILITATE", style="Title"))
    body.extend(build_exercise_section(report))
    body.extend(build_downstream_section(report))
    body.extend(build_upstream_section(report))
    body.extend(build_production_section(report))
    body.extend(build_lot_flow_and_documents_section(report))
    body.extend(build_conclusion_section(report))
    body.extend(build_sources_section(report))
    return wrap_document("".join(body))


def build_exercise_section(report: AuditTraceabilityReport) -> list[str]:
    exercise = report.exercise
    balance = report.balance
    return [
        paragraph("01_EXERCITIU — Fișa principală a exercițiului", style="Heading1"),
        table(
            ["Câmp", "Valoare"],
            [
                ["Cod articol", exercise.code],
                ["Lot", exercise.lot],
                ["Denumire produs", exercise.product_name],
                ["Tip caz", exercise.case_type],
                ["Status trasabilitate", exercise.traceability_result],
                ["Data generării", date.today().isoformat()],
            ],
        ),
        paragraph("Bilanț produs finit", style="Heading2"),
        table(
            ["Indicator", "Cantitate", "UM", "Observație"],
            [
                ["PRD produs", balance.prd_produced_quantity, balance.prd_produced_um, "Sursă PRD"],
                ["WMS PRODUCTION-OUT", balance.wms_production_out_quantity, balance.wms_production_out_um, "Sursă WMS"],
                ["WMS livrat", balance.wms_delivered_quantity, balance.wms_delivered_um, "Valori WMS semnate"],
                ["Stoc la moment", balance.stock_quantity, balance.stock_um, "Dacă există în fișierul stoc"],
                ["Corecții / ajustări", balance.adjustments_quantity, balance.adjustments_um, "Se verifică documentar"],
            ],
        ),
        paragraph(f"Status bilanț: {balance.balance_status}"),
        paragraph(f"Observație bilanț: {balance.balance_observation}"),
    ]


def build_downstream_section(report: AuditTraceabilityReport) -> list[str]:
    rows = [[d.order_number, d.document_number, d.client, d.quantity, d.um, d.delivery_date] for d in report.downstream]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE", "FARA DATE IDENTIFICATE"]]
    return [
        paragraph("03_TABEL_II_AVAL — Livrări produs finit", style="Heading1"),
        paragraph("Livrările produsului finit sunt preluate din WMS."),
        table(["Comandă WMS", "Document", "Client", "Cantitate", "UM", "Dată"], rows),
    ]


def build_upstream_section(report: AuditTraceabilityReport) -> list[str]:
    rows = [
        [line.category, line.code, line.lot, line.name, line.quantity_consumed, line.um, line.third_party_delivery_status, line.stock_at_moment, "; ".join(line.observations)]
        for line in report.upstream
    ]
    if not rows:
        rows = [["FARA DATE IDENTIFICATE"] * 9]
    return [
        paragraph("02_TABEL_I_AMONTE — Materii prime, ambalaje și materiale auxiliare", style="Heading1"),
        paragraph("Pentru materiile prime se păstrează explicit verificarea livrărilor către terți."),
        table(["Categorie", "Cod", "Lot", "Denumire", "Cantitate", "UM", "Livrări terți", "Stoc", "Observații"], rows),
    ]


def build_production_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [paragraph("04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție", style="Heading1")]
    if not report.production_orders:
        return parts + [paragraph("FARA DATE IDENTIFICATE")]
    for order in report.production_orders:
        parts.extend(build_production_order_block(order))
    return parts


def build_production_order_block(order: ProductionOrderTrace) -> list[str]:
    parts = [
        paragraph(f"Comanda producție {order.production_order}", style="Heading2"),
        table(
            ["Câmp", "Valoare"],
            [
                ["Produs finit", order.finished_product_name],
                ["Cod / lot", f"{order.finished_product_code} / {order.finished_product_lot}"],
                ["Cantitate PRD", f"{order.prd_quantity} {order.prd_um}"],
                ["WMS PRODUCTION-OUT", f"{order.wms_production_out_quantity} {order.wms_production_out_um}"],
                ["Livrare asociată", order.associated_delivery],
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
    headers = ["Cod", "Lot", "Denumire", "Cantitate", "UM"]
    if include_third_party:
        headers.append("Livrări către terți")
    rows = []
    for line in lines:
        row = [line.code, line.lot, line.name, line.quantity_consumed, line.um]
        if include_third_party:
            row.append(line.third_party_delivery_status)
        rows.append(row)
    return [paragraph(title, style="Heading2"), table(headers, rows)]


def build_lot_flow_and_documents_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [paragraph("05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente fizice", style="Heading1")]
    flow_rows = [
        [flow.category, flow.code, flow.lot, flow.name, flow.consumed_in_audited_lot, flow.third_party_delivered_total, flow.stock_at_moment, flow.observation]
        for flow in report.source_lot_flows
    ]
    if not flow_rows:
        flow_rows = [["FARA DATE IDENTIFICATE"] * 8]
    parts.append(paragraph("Fluxuri loturi sursă", style="Heading2"))
    parts.append(table(["Categorie", "Cod", "Lot", "Denumire", "Consum în lot", "Livrări terți", "Stoc", "Observație"], flow_rows))
    parts.append(paragraph("Registru documente fizice necesare", style="Heading2"))
    parts.append(table(["Arie", "Tip document", "Referință", "Cod", "Lot", "Comandă", "De ce este necesar", "Status"], document_rows(report.physical_documents)))
    return parts


def document_rows(documents: list[PhysicalDocumentRequirement]) -> list[list[str]]:
    if not documents:
        return [["FARA DATE IDENTIFICATE"] * 8]
    return [[doc.document_area, doc.document_type, doc.document_reference, doc.related_code, doc.related_lot, doc.related_order, doc.why_needed, doc.status] for doc in documents]


def build_conclusion_section(report: AuditTraceabilityReport) -> list[str]:
    parts = [
        paragraph("Concluzie audit intern", style="Heading1"),
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
    ]


def table(headers: list[str], rows: list[list[object]]) -> str:
    xml_rows = [table_row(headers, is_header=True)]
    xml_rows.extend(table_row(row) for row in rows)
    borders = "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/></w:tblBorders>"
    return f"<w:tbl><w:tblPr><w:tblStyle w:val=\"TraceAITable\"/><w:tblW w:w=\"0\" w:type=\"auto\"/>{borders}</w:tblPr>{''.join(xml_rows)}</w:tbl>"


def table_row(values: Iterable[object], is_header: bool = False) -> str:
    return f"<w:tr>{''.join(table_cell(value, is_header=is_header) for value in values)}</w:tr>"


def table_cell(value: object, is_header: bool = False) -> str:
    shading_xml = '<w:shd w:fill="D9EAF7"/>' if is_header else ""
    bold_xml = "<w:b/>" if is_header else ""
    return f"<w:tc><w:tcPr>{shading_xml}</w:tcPr><w:p><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{escape(value_or_missing(value))}</w:t></w:r></w:p></w:tc>"


def paragraph(text: object, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{escape(value_or_missing(text))}</w:t></w:r></w:p>"


def bullets(items: Iterable[object]) -> list[str]:
    return [paragraph(f"• {value_or_missing(item)}") for item in items]


def value_or_missing(value: object) -> str:
    if value is None:
        return "FARA DATE IDENTIFICATE"
    text = str(value).strip()
    return text if text else "FARA DATE IDENTIFICATE"


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
      <w:pgMar w:top="1000" w:right="900" w:bottom="1000" w:left="900" w:header="720" w:footer="720" w:gutter="0"/>
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
