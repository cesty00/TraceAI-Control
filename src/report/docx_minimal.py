"""
Minimal DOCX report generator for TraceAI Control.

Faza 5 scope:
- generate a narrative DOCX from TraceabilityCase;
- do not read operational source files directly;
- mark missing sections explicitly.

The implementation builds a valid DOCX package using only the Python standard
library so the first report engine step has no external runtime dependency.
"""

from __future__ import annotations

import argparse
import html
import zipfile
from pathlib import Path
from typing import Iterable

from src.rules.run_traceability_case import run_traceability_case
from src.rules.traceability_case import TraceabilityCase

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
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
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>TraceAI Control</Application>
</Properties>
"""

CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Raport trasabilitate TraceAI Control</dc:title>
  <dc:creator>TraceAI Control</dc:creator>
</cp:coreProperties>
"""


def generate_minimal_docx_report(traceability_case: TraceabilityCase, output_path: str | Path) -> Path:
    """Generate a minimal narrative DOCX from TraceabilityCase."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    document_xml = build_document_xml(traceability_case)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        package.writestr("_rels/.rels", ROOT_RELS_XML)
        package.writestr("docProps/app.xml", APP_XML)
        package.writestr("docProps/core.xml", CORE_XML)
        package.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
        package.writestr("word/document.xml", document_xml)

    return output


def build_document_xml(traceability_case: TraceabilityCase) -> str:
    """Build WordprocessingML for the minimal report."""

    body_parts: list[str] = []
    body_parts.append(paragraph("Raport de trasabilitate", style="Title"))
    body_parts.append(paragraph("Generat din TraceabilityCase. Document narativ minimal pentru audit."))

    subject = traceability_case.subject
    body_parts.append(paragraph("1. Subiectul raportului", style="Heading1"))
    body_parts.extend(
        bullet_list(
            [
                f"Cod articol/produs: {value_or_missing(subject.code)}",
                f"Lot: {value_or_missing(subject.lot)}",
                f"Tip caz detectat: {value_or_missing(subject.case_type)}",
            ]
        )
    )

    body_parts.append(paragraph("2. Dovezi folosite", style="Heading1"))
    if traceability_case.evidence:
        body_parts.extend(
            bullet_list(
                [
                    format_evidence(item.source_key, item.source_name, item.sheet_name, item.row_number, item.message)
                    for item in traceability_case.evidence
                ]
            )
        )
    else:
        body_parts.append(paragraph("FARA DATE IDENTIFICATE"))

    body_parts.append(paragraph("3. Observații", style="Heading1"))
    if traceability_case.observations:
        body_parts.extend(bullet_list(traceability_case.observations))
    else:
        body_parts.append(paragraph("Nu există observații suplimentare."))

    body_parts.append(paragraph("4. Secțiuni tehnice", style="Heading1"))
    if traceability_case.sections:
        body_parts.extend(
            bullet_list(
                [f"{key}: {value_or_missing(value)}" for key, value in traceability_case.sections.items()]
            )
        )
    else:
        body_parts.append(paragraph("FARA DATE IDENTIFICATE"))

    body_parts.append(paragraph("5. Secțiuni fără date", style="Heading1"))
    body_parts.extend(
        bullet_list(
            [
                "Trasabilitate amonte detaliată: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
                "Trasabilitate aval detaliată: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
                "Bilanț stoc detaliat: FARA DATE IDENTIFICATE în TraceabilityCase minimal.",
            ]
        )
    )

    return wrap_document("".join(body_parts))


def paragraph(text: object, style: str | None = None) -> str:
    """Return one WordprocessingML paragraph."""

    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{escape_text(value_or_missing(text))}</w:t></w:r></w:p>"


def bullet_list(items: Iterable[object]) -> list[str]:
    """Return simple bullet-like paragraphs."""

    return [paragraph(f"• {value_or_missing(item)}") for item in items]


def format_evidence(
    source_key: str,
    source_name: str,
    sheet_name: str | None,
    row_number: int | None,
    message: str,
) -> str:
    sheet = sheet_name if sheet_name else "fără sheet"
    row = row_number if row_number is not None else "fără rând"
    return f"{source_key} / {source_name} / {sheet} / {row}: {message}"


def value_or_missing(value: object) -> str:
    """Return explicit missing marker for empty values."""

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
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genereaza raport DOCX minimal din TraceabilityCase."
    )
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
