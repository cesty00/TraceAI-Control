"""Narrative DOCX report generator for TraceAI Control."""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from datetime import date
from pathlib import Path
from typing import Iterable

from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import (
    TraceabilityCase,
    TraceabilityReportTable,
    TraceabilityTableRow,
    report_tables_as_list,
)

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
  <dc:title>Raport trasabilitate TraceAI Control</dc:title>
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
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:rPr><w:b/><w:color w:val="1F4E79"/></w:rPr><w:t>TraceAI Control — Raport de trasabilitate</w:t></w:r></w:p></w:hdr>
"""

FOOTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Document generat din TraceabilityCase. Uz intern / audit.</w:t></w:r></w:p></w:ftr>
"""

SOURCE_LABELS = {"wms": "WMS", "production": "PRD", "nomenclator": "nomenclator", "stock": "stoc la moment"}
CASE_TYPE_LABELS = {
    "FINISHED_PRODUCT": "produs finit",
    "RAW_MATERIAL": "materie primă",
    "WMS_ONLY_PRODUCT": "produs fără flux de producție identificat",
    "UNKNOWN": "necunoscut / date insuficiente",
}


def generate_minimal_docx_report(traceability_case: TraceabilityCase, output_path: str | Path) -> Path:
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
        package.writestr("word/document.xml", build_document_xml(traceability_case))
    return output


def build_document_xml(traceability_case: TraceabilityCase) -> str:
    body_parts: list[str] = []
    body_parts.extend(build_report_header(traceability_case))
    body_parts.extend(build_report_metadata(traceability_case))
    body_parts.extend(build_executive_summary(traceability_case))
    body_parts.extend(build_case_identification(traceability_case))
    body_parts.extend(build_sources_section(traceability_case))
    body_parts.extend(build_case_type_interpretation(traceability_case))
    body_parts.extend(build_evidence_section(traceability_case))
    body_parts.extend(build_observations_section(traceability_case))
    body_parts.extend(build_report_tables_section(traceability_case))
    body_parts.extend(build_preliminary_balance_section(traceability_case))
    body_parts.extend(build_missing_data_section(traceability_case))
    body_parts.extend(build_preliminary_conclusion(traceability_case))
    body_parts.extend(build_operational_recommendation(traceability_case))
    body_parts.extend(build_audit_documents_section())
    body_parts.extend(build_signatures_section())
    return wrap_document("".join(body_parts))


def build_report_header(traceability_case: TraceabilityCase) -> list[str]:
    subject = traceability_case.subject
    return [
        paragraph("RAPORT DE TRASABILITATE", style="Title"),
        paragraph(f"Articol verificat: {value_or_missing(subject.code)}"),
        paragraph(f"Lot verificat: {value_or_missing(subject.lot)}"),
        paragraph("Produs: FARA DATE IDENTIFICATE în TraceabilityCase minimal."),
        paragraph(f"Data generării: {date.today().isoformat()}"),
        paragraph("Caracter document: Preliminar / uz intern / audit"),
        paragraph(f"Surse utilizate: {format_used_sources(traceability_case)}"),
    ]


def build_report_metadata(traceability_case: TraceabilityCase) -> list[str]:
    subject = traceability_case.subject
    table = TraceabilityReportTable(
        key="report_metadata",
        title="Metadate raport",
        columns=["Câmp", "Valoare"],
        rows=[
            metadata_row("Cod articol", subject.code),
            metadata_row("Lot", subject.lot),
            metadata_row("Tip caz", subject.case_type),
            metadata_row("Status validare Core", traceability_case.sections.get("core_validation_status")),
            metadata_row("Număr înregistrări selectate", traceability_case.sections.get("selected_record_count")),
            metadata_row("Data generării", date.today().isoformat()),
        ],
        empty_message="Nu au fost identificate metadate raport.",
    )
    return [paragraph("0. Metadate raport", style="Heading1"), word_table(table)]


def metadata_row(label: object, value: object) -> TraceabilityTableRow:
    return TraceabilityTableRow(values={"Câmp": value_or_missing(label), "Valoare": value_or_missing(value)})


def build_executive_summary(traceability_case: TraceabilityCase) -> list[str]:
    subject = traceability_case.subject
    case_label = CASE_TYPE_LABELS.get(subject.case_type, subject.case_type)
    selected_count = traceability_case.sections.get("selected_record_count")
    return [
        paragraph("1. Rezumat executiv", style="Heading1"),
        paragraph(
            f"Raportul prezintă verificarea de trasabilitate pentru articolul {value_or_missing(subject.code)}, "
            f"lot {value_or_missing(subject.lot)}. Tipul de caz detectat este {value_or_missing(case_label)}. "
            f"Numărul de înregistrări selectate în etapa Core este {value_or_missing(selected_count)}."
        ),
        paragraph(
            "Documentul este generat din TraceabilityCase și are caracter preliminar. "
            "Tabelele operaționale sunt afișate numai dacă există în TraceabilityCase."
        ),
    ]


def build_case_identification(traceability_case: TraceabilityCase) -> list[str]:
    subject = traceability_case.subject
    return [
        paragraph("2. Identificarea cazului", style="Heading1"),
        *bullet_list(
            [
                f"Cod articol/produs: {value_or_missing(subject.code)}",
                f"Lot: {value_or_missing(subject.lot)}",
                f"Tip caz detectat: {value_or_missing(subject.case_type)}",
                f"Status validare Core: {value_or_missing(traceability_case.sections.get('core_validation_status'))}",
            ]
        ),
    ]


def build_sources_section(traceability_case: TraceabilityCase) -> list[str]:
    sources = sorted({item.source_key for item in traceability_case.evidence})
    items = [f"{SOURCE_LABELS.get(source, source)} ({source})" for source in sources] if sources else ["FARA DATE IDENTIFICATE în dovezile TraceabilityCase."]
    return [
        paragraph("3. Surse utilizate", style="Heading1"),
        paragraph("Sursele sunt preluate indirect prin TraceabilityCase, nu prin citirea directă a fișierelor operaționale."),
        *bullet_list(items),
    ]


def build_case_type_interpretation(traceability_case: TraceabilityCase) -> list[str]:
    return [paragraph("4. Interpretarea tipului de caz", style="Heading1"), paragraph(case_type_narrative(traceability_case.subject.code, traceability_case.subject.lot, traceability_case.subject.case_type))]


def build_evidence_section(traceability_case: TraceabilityCase) -> list[str]:
    paragraphs = [paragraph("5. Dovezi folosite", style="Heading1")]
    if traceability_case.evidence:
        paragraphs.extend(
            bullet_list(
                [format_evidence(item.source_key, item.source_name, item.sheet_name, item.row_number, item.message) for item in traceability_case.evidence]
            )
        )
    else:
        paragraphs.append(paragraph("FARA DATE IDENTIFICATE"))
    return paragraphs


def build_observations_section(traceability_case: TraceabilityCase) -> list[str]:
    paragraphs = [paragraph("6. Observații tehnice", style="Heading1")]
    paragraphs.extend(bullet_list(traceability_case.observations) if traceability_case.observations else [paragraph("Nu există observații suplimentare în TraceabilityCase.")])
    if traceability_case.sections:
        paragraphs.append(paragraph("Metadate tehnice disponibile", style="Heading2"))
        paragraphs.extend(bullet_list([f"{key}: {value_or_missing(value)}" for key, value in traceability_case.sections.items()]))
    return paragraphs


def build_report_tables_section(traceability_case: TraceabilityCase) -> list[str]:
    paragraphs = [
        paragraph("7. Tabele operaționale din TraceabilityCase", style="Heading1"),
        paragraph("Tabelele de mai jos sunt randate exclusiv din TraceabilityCase. Report Engine nu citește fișierele sursă."),
    ]
    for table in report_tables_as_list(traceability_case.report_tables):
        paragraphs.extend(build_report_table(table))
    return paragraphs


def build_preliminary_balance_section(traceability_case: TraceabilityCase) -> list[str]:
    balance = traceability_case.preliminary_balance
    paragraphs = [
        paragraph("8. Bilanț preliminar", style="Heading1"),
        paragraph("Bilanțul preliminar este preluat din TraceabilityCase și este conservator. Nu se fac conversii automate de unități de măsură și nu se deduc fluxuri lipsă."),
    ]
    if balance.messages:
        paragraphs.append(paragraph("Mesaje bilanț", style="Heading2"))
        paragraphs.extend(bullet_list(balance.messages))
    table = TraceabilityReportTable(
        key="preliminary_balance",
        title="Linii bilanț preliminar",
        columns=["Tabel", "Coloană", "UM", "Total", "Rânduri sursă", "Rânduri ignorate", "Mesaj"],
        rows=[
            TraceabilityTableRow(
                values={
                    "Tabel": line.table_title,
                    "Coloană": line.quantity_column,
                    "UM": line.unit,
                    "Total": line.total,
                    "Rânduri sursă": str(line.source_row_count),
                    "Rânduri ignorate": str(line.skipped_row_count),
                    "Mesaj": line.message,
                }
            )
            for line in balance.lines
        ],
        empty_message="Nu există linii de bilanț preliminar calculate în TraceabilityCase.",
    )
    paragraphs.extend(build_report_table(table))
    return paragraphs


def build_report_table(table: TraceabilityReportTable) -> list[str]:
    return [paragraph(table.title, style="Heading2"), word_table(table)]


def word_table(table: TraceabilityReportTable) -> str:
    rows = [word_table_row(table.columns, is_header=True)]
    if not table.rows:
        rows.append(word_table_row([table.empty_message], grid_span=max(1, len(table.columns))))
    else:
        for row in table.rows:
            rows.append(word_table_row([value_or_missing(get_table_value(row.values, column)) for column in table.columns]))
            if any([row.source_key, row.source_name, row.sheet_name, row.row_number]):
                rows.append(word_table_row([f"Sursă: {format_row_source(row.source_key, row.source_name, row.sheet_name, row.row_number)}"], grid_span=max(1, len(table.columns))))
    borders = "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/><w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"BFBFBF\"/></w:tblBorders>"
    return f"<w:tbl><w:tblPr><w:tblStyle w:val=\"TraceAITable\"/><w:tblW w:w=\"0\" w:type=\"auto\"/>{borders}</w:tblPr>{''.join(rows)}</w:tbl>"


def get_table_value(values: dict[str, str], column: str) -> str | None:
    """Return a table value using display-column tolerant matching.

    Source rows may contain normalized keys such as ``document_comanda`` while
    report tables expose display labels such as ``Document comanda``. This
    lookup keeps Report Engine read-only and avoids business inference.
    """

    if column in values:
        return values[column]

    folded_column = column.casefold()
    for key, value in values.items():
        if key.casefold() == folded_column:
            return value

    normalized_column = normalize_table_key(column)
    for key, value in values.items():
        if normalize_table_key(key) == normalized_column:
            return value

    return None


def normalize_table_key(value: object) -> str:
    text = remove_diacritics(str(value)).casefold().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def remove_diacritics(value: str) -> str:
    return value.translate(
        str.maketrans(
            {
                "ă": "a",
                "â": "a",
                "î": "i",
                "ș": "s",
                "ş": "s",
                "ț": "t",
                "ţ": "t",
                "Ă": "A",
                "Â": "A",
                "Î": "I",
                "Ș": "S",
                "Ş": "S",
                "Ț": "T",
                "Ţ": "T",
            }
        )
    )


def word_table_row(values: Iterable[object], is_header: bool = False, grid_span: int | None = None) -> str:
    return f"<w:tr>{''.join(word_table_cell(value, is_header=is_header, grid_span=grid_span if index == 0 else None) for index, value in enumerate(values))}</w:tr>"


def word_table_cell(value: object, is_header: bool = False, grid_span: int | None = None) -> str:
    grid_span_xml = f'<w:gridSpan w:val="{grid_span}"/>' if grid_span and grid_span > 1 else ""
    shading_xml = '<w:shd w:fill="D9EAF7"/>' if is_header else ""
    bold_xml = "<w:b/>" if is_header else ""
    return f"<w:tc><w:tcPr>{grid_span_xml}{shading_xml}</w:tcPr><w:p><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{escape_text(value_or_missing(value))}</w:t></w:r></w:p></w:tc>"


def format_row_source(source_key: str | None, source_name: str | None, sheet_name: str | None, row_number: int | None) -> str:
    return " / ".join([value_or_missing(source_key), value_or_missing(source_name), value_or_missing(sheet_name), value_or_missing(row_number)])


def build_missing_data_section(traceability_case: TraceabilityCase) -> list[str]:
    return [
        paragraph("9. Secțiuni fără date", style="Heading1"),
        paragraph("Secțiunile de mai jos nu sunt lăsate goale; lipsa datelor este marcată explicit."),
        *bullet_list(missing_data_messages(traceability_case.subject.case_type)),
    ]


def build_preliminary_conclusion(traceability_case: TraceabilityCase) -> list[str]:
    subject = traceability_case.subject
    return [paragraph("10. Concluzie preliminară", style="Heading1"), paragraph(preliminary_conclusion(subject.code, subject.lot, subject.case_type, bool(traceability_case.evidence)))]


def build_operational_recommendation(traceability_case: TraceabilityCase) -> list[str]:
    recommendations = {
        "FINISHED_PRODUCT": "Verificați manual comenzile de producție, documentele WMS și documentele de livrare asociate lotului.",
        "RAW_MATERIAL": "Verificați manual recepția WMS, consumurile în producție și eventualele livrări către terți.",
        "WMS_ONLY_PRODUCT": "Verificați manual documentele WMS de recepție/livrare și confirmați lipsa fluxului PRD.",
        "UNKNOWN": "Completați sau corectați sursele operaționale înainte de utilizarea raportului în audit.",
    }
    return [paragraph("11. Recomandare operațională", style="Heading1"), paragraph(recommendations.get(traceability_case.subject.case_type, "Verificați manual sursele operaționale relevante înainte de audit."))]


def build_audit_documents_section() -> list[str]:
    return [
        paragraph("12. Documente de pregătit pentru audit", style="Heading1"),
        *bullet_list(
            [
                "Documente WMS: Numar comanda, Document intrare, Document comanda, unde există.",
                "Rapoarte de producție PRD aferente codului și lotului verificat, unde există.",
                "Extras nomenclator pentru articolul verificat.",
                "Situația stocului la momentul verificării.",
            ]
        ),
    ]


def build_signatures_section() -> list[str]:
    return [
        paragraph("13. Semnături", style="Heading1"),
        paragraph("Întocmit de: ______________________________"),
        paragraph("Verificat de: ______________________________"),
        paragraph("Luare la cunoștință: ________________________"),
    ]


def case_type_narrative(code: str, lot: str, case_type: str) -> str:
    code_text = value_or_missing(code)
    lot_text = value_or_missing(lot)
    if case_type == "FINISHED_PRODUCT":
        return f"Pentru articolul {code_text}, lot {lot_text}, au fost identificate indicii de producție. Cazul este tratat ca produs finit, iar raportul trebuie completat ulterior cu producție, aval și amonte detaliat."
    if case_type == "RAW_MATERIAL":
        return f"Pentru articolul {code_text}, lot {lot_text}, clasificarea indică materie primă. Raportul trebuie completat ulterior cu recepții, consumuri și produse finite rezultate."
    if case_type == "WMS_ONLY_PRODUCT":
        return f"Pentru articolul {code_text}, lot {lot_text}, nu au fost identificate înregistrări de producție relevante. Trasabilitatea este tratată ca WMS-only și se bazează pe datele WMS disponibile în TraceabilityCase."
    return f"Pentru articolul {code_text}, lot {lot_text}, datele disponibile nu sunt suficiente pentru o încadrare operațională completă."


def preliminary_conclusion(code: str, lot: str, case_type: str, has_evidence: bool) -> str:
    if not has_evidence:
        return f"Pentru articolul {value_or_missing(code)}, lot {value_or_missing(lot)}, TraceabilityCase nu conține dovezi suficiente. Concluzia preliminară este că verificarea trebuie reluată după completarea datelor."
    if case_type == "UNKNOWN":
        return f"Pentru articolul {value_or_missing(code)}, lot {value_or_missing(lot)}, există unele date, dar ele nu permit încă stabilirea tipului de caz."
    return f"Pentru articolul {value_or_missing(code)}, lot {value_or_missing(lot)}, raportul a identificat un caz de tip {case_type}. Concluzia este preliminară și trebuie confirmată prin verificarea documentelor operaționale suport."


def missing_data_messages(case_type: str) -> list[str]:
    common = [
        "Denumire produs: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
        "Numar comanda / Document intrare / Document comanda: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
        "Stoc la moment detaliat: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
    ]
    if case_type == "FINISHED_PRODUCT":
        return common + [
            "Situația numerică utilizată în verificare: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "AVAL produs finit: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "AMONTE materii prime alimentare: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "AMONTE ambalaje: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "AMONTE materiale auxiliare / gaz: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
        ]
    if case_type == "RAW_MATERIAL":
        return common + [
            "Recepția lotului: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Consumuri în producție: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Produse finite rezultate: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Livrări directe către terți: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
        ]
    if case_type == "WMS_ONLY_PRODUCT":
        return common + [
            "Recepția lotului: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Livrarea lotului: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Bilanț recepționat-livrat-stoc: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            "Flux PRD: Nu au fost identificate înregistrări PRD pentru acest articol și lot.",
        ]
    return common + ["Încadrarea cazului: FARA DATE SUFICIENTE pentru interpretare completă."]


def format_used_sources(traceability_case: TraceabilityCase) -> str:
    sources = sorted({item.source_key for item in traceability_case.evidence})
    return ", ".join(SOURCE_LABELS.get(source, source) for source in sources) if sources else "FARA DATE IDENTIFICATE"


def paragraph(text: object, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{escape_text(value_or_missing(text))}</w:t></w:r></w:p>"


def bullet_list(items: Iterable[object]) -> list[str]:
    return [paragraph(f"• {value_or_missing(item)}") for item in items]


def format_evidence(source_key: str, source_name: str, sheet_name: str | None, row_number: int | None, message: str) -> str:
    return f"{source_key} / {source_name} / {sheet_name if sheet_name else 'fără sheet'} / {row_number if row_number is not None else 'fără rând'}: {message}"


def value_or_missing(value: object) -> str:
    if value is None:
        return "FARA DATE IDENTIFICATE"
    text = str(value).strip()
    return text if text else "FARA DATE IDENTIFICATE"


def escape_text(value: str) -> str:
    return html.escape(value, quote=False)


def wrap_document(body_xml: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_xml}
    <w:sectPr>
      <w:headerReference w:type="default" r:id="rIdHeader1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
      <w:footerReference w:type="default" r:id="rIdFooter1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genereaza raport DOCX narativ din TraceabilityCase.")
    parser.add_argument("source_directory", help="Folderul cu sursele oficiale.")
    parser.add_argument("--code", required=True, help="Cod articol/produs cautat.")
    parser.add_argument("--lot", required=True, help="Lot cautat.")
    parser.add_argument("--output", "-o", required=True, help="Cale output DOCX.")
    args = parser.parse_args(argv)
    traceability_case = run_traceability_case(args.source_directory, args.code, args.lot)
    generate_minimal_docx_report(traceability_case, args.output)
    return 0 if traceability_case.subject.case_type != "UNKNOWN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
